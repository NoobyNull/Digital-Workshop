/**
 * CUDA kernel for GPU-accelerated STL triangle processing.
 *
 * This kernel processes raw STL binary data to extract triangle geometry
 * and compute normals, optimized for parallel execution on NVIDIA GPUs.
 *
 * Performance targets:
 * - 10-20x speedup over CPU processing for large models
 * - Memory-efficient processing with minimal host-device transfers
 * - Support for up to 10M triangles per kernel launch
 */

#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#include <math.h>

// STL triangle structure (50 bytes total)
struct STLTriangle {
    float normal[3];      // 12 bytes
    float vertices[9];    // 36 bytes (3 vertices × 3 floats)
    unsigned short attr;  // 2 bytes (attribute byte count)
};

// Output vertex structure for VTK integration
struct ProcessedVertex {
    float position[3];
    float normal[3];
};

/**
 * Kernel to process STL triangles and extract vertex/normal data.
 *
 * Each thread processes one triangle from the raw STL data.
 * Outputs are stored in separate vertex and normal arrays for efficient
 * memory access patterns in downstream processing.
 *
 * @param stl_data Raw STL triangle data (50 bytes per triangle)
 * @param vertex_output Output vertex array (9 floats per triangle)
 * @param normal_output Output normal array (3 floats per triangle, repeated 3x)
 * @param triangle_count Total number of triangles to process
 */
__global__ void process_stl_triangles_kernel(
    const unsigned char* stl_data,
    float* vertex_output,
    float* normal_output,
    const unsigned int triangle_count
) {
    // Calculate global triangle index
    const unsigned int triangle_idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Bounds check
    if (triangle_idx >= triangle_count) {
        return;
    }

    // Calculate input data offset (50 bytes per triangle)
    const size_t data_offset = triangle_idx * 50;

    // Extract normal vector (first 12 bytes, little-endian floats)
    const float* normal_ptr = reinterpret_cast<const float*>(&stl_data[data_offset]);
    float nx = normal_ptr[0];
    float ny = normal_ptr[1];
    float nz = normal_ptr[2];

    // Extract vertex data (next 36 bytes, 9 floats)
    const float* vertex_ptr = reinterpret_cast<const float*>(&stl_data[data_offset + 12]);
    float v1x = vertex_ptr[0], v1y = vertex_ptr[1], v1z = vertex_ptr[2];
    float v2x = vertex_ptr[3], v2y = vertex_ptr[4], v2z = vertex_ptr[5];
    float v3x = vertex_ptr[6], v3y = vertex_ptr[7], v3z = vertex_ptr[8];

    // Calculate output offsets
    const size_t vertex_out_offset = triangle_idx * 9;  // 9 floats per triangle
    const size_t normal_out_offset = triangle_idx * 9;  // 3 normals × 3 floats each

    // Store vertices (interleaved: v1x,v1y,v1z,v2x,v2y,v2z,v3x,v3y,v3z)
    vertex_output[vertex_out_offset + 0] = v1x;
    vertex_output[vertex_out_offset + 1] = v1y;
    vertex_output[vertex_out_offset + 2] = v1z;
    vertex_output[vertex_out_offset + 3] = v2x;
    vertex_output[vertex_out_offset + 4] = v2y;
    vertex_output[vertex_out_offset + 5] = v2z;
    vertex_output[vertex_out_offset + 6] = v3x;
    vertex_output[vertex_out_offset + 7] = v3y;
    vertex_output[vertex_out_offset + 8] = v3z;

    // Store normals (repeated 3 times, one per vertex)
    #pragma unroll
    for (int i = 0; i < 3; ++i) {
        const size_t normal_idx = normal_out_offset + i * 3;
        normal_output[normal_idx + 0] = nx;
        normal_output[normal_idx + 1] = ny;
        normal_output[normal_idx + 2] = nz;
    }
}

/**
 * Kernel to compute bounding box from vertex data.
 *
 * Processes vertex array to find min/max bounds using parallel reduction.
 * Each block computes partial min/max, final reduction done on host.
 *
 * @param vertices Input vertex array (x,y,z,x,y,z,... format)
 * @param vertex_count Total number of vertices (3 per triangle)
 * @param partial_mins Output array for block-level min values
 * @param partial_maxs Output array for block-level max values
 */
__global__ void compute_bounds_kernel(
    const float* vertices,
    const unsigned int vertex_count,
    float* partial_mins,
    float* partial_maxs
) {
    // Shared memory for block-level reduction
    __shared__ float shared_min[3];
    __shared__ float shared_max[3];

    // Initialize shared memory
    if (threadIdx.x == 0) {
        shared_min[0] = INFINITY;
        shared_min[1] = INFINITY;
        shared_min[2] = INFINITY;
        shared_max[0] = -INFINITY;
        shared_max[1] = -INFINITY;
        shared_max[2] = -INFINITY;
    }
    __syncthreads();

    // Each thread processes multiple vertices for better occupancy
    const unsigned int stride = blockDim.x * gridDim.x;
    float local_min[3] = {INFINITY, INFINITY, INFINITY};
    float local_max[3] = {-INFINITY, -INFINITY, -INFINITY};

    for (unsigned int i = threadIdx.x + blockIdx.x * blockDim.x; i < vertex_count; i += stride) {
        const unsigned int base_idx = i * 3;
        const float x = vertices[base_idx + 0];
        const float y = vertices[base_idx + 1];
        const float z = vertices[base_idx + 2];

        local_min[0] = fminf(local_min[0], x);
        local_min[1] = fminf(local_min[1], y);
        local_min[2] = fminf(local_min[2], z);

        local_max[0] = fmaxf(local_max[0], x);
        local_max[1] = fmaxf(local_max[1], y);
        local_max[2] = fmaxf(local_max[2], z);
    }

    // Reduce within block
    atomicMinFloat(&shared_min[0], local_min[0]);
    atomicMinFloat(&shared_min[1], local_min[1]);
    atomicMinFloat(&shared_min[2], local_min[2]);

    atomicMaxFloat(&shared_max[0], local_max[0]);
    atomicMaxFloat(&shared_max[1], local_max[1]);
    atomicMaxFloat(&shared_max[2], local_max[2]);

    __syncthreads();

    // Write block results to global memory
    if (threadIdx.x == 0) {
        const unsigned int block_idx = blockIdx.x * 3;
        partial_mins[block_idx + 0] = shared_min[0];
        partial_mins[block_idx + 1] = shared_min[1];
        partial_mins[block_idx + 2] = shared_min[2];

        partial_maxs[block_idx + 0] = shared_max[0];
        partial_maxs[block_idx + 1] = shared_max[1];
        partial_maxs[block_idx + 2] = shared_max[2];
    }
}

/**
 * Kernel to validate STL triangle data integrity.
 *
 * Checks for NaN/inf values and degenerate triangles.
 * Outputs validation flags for each triangle.
 *
 * @param vertices Input vertex array
 * @param triangle_count Number of triangles to validate
 * @param validation_flags Output flags (0=valid, 1=invalid)
 */
__global__ void validate_triangles_kernel(
    const float* vertices,
    const unsigned int triangle_count,
    unsigned char* validation_flags
) {
    const unsigned int triangle_idx = blockIdx.x * blockDim.x + threadIdx.x;

    if (triangle_idx >= triangle_count) {
        return;
    }

    const size_t vertex_offset = triangle_idx * 9;
    unsigned char is_valid = 1;

    // Check for NaN or infinite values
    #pragma unroll
    for (int i = 0; i < 9; ++i) {
        const float val = vertices[vertex_offset + i];
        if (isnan(val) || isinf(val)) {
            is_valid = 0;
            break;
        }
    }

    // Check for degenerate triangles (zero area)
    if (is_valid) {
        const float* v1 = &vertices[vertex_offset + 0];
        const float* v2 = &vertices[vertex_offset + 3];
        const float* v3 = &vertices[vertex_offset + 6];

        // Compute cross product to check area
        const float ux = v2[0] - v1[0], uy = v2[1] - v1[1], uz = v2[2] - v1[2];
        const float vx = v3[0] - v1[0], vy = v3[1] - v1[1], vz = v3[2] - v1[2];

        const float cross_x = uy * vz - uz * vy;
        const float cross_y = uz * vx - ux * vz;
        const float cross_z = ux * vy - uy * vx;

        const float area_squared = cross_x*cross_x + cross_y*cross_y + cross_z*cross_z;

        if (area_squared < 1e-12f) {  // Very small area threshold
            is_valid = 0;
        }
    }

    validation_flags[triangle_idx] = is_valid;
}

// Helper functions for atomic operations on floats (CUDA < 11.0 compatibility)
__device__ float atomicMinFloat(float* addr, float val) {
    return atomicMin((int*)addr, __float_as_int(val));
}

__device__ float atomicMaxFloat(float* addr, float val) {
    return atomicMax((int*)addr, __float_as_int(val));
}
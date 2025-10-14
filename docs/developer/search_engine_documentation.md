# Search Engine Documentation

## Overview

The 3D-MM application includes a powerful search engine built on SQLite FTS5 (Full-Text Search) technology. This search system provides fast, efficient searching across model metadata with advanced filtering, search history, and saved searches functionality.

## Architecture

### Core Components

1. **SearchEngine** (`src/core/search_engine.py`)
   - Main search engine implementation using SQLite FTS5
   - Handles full-text search, filtering, and search management
   - Thread-safe operations with proper logging

2. **SearchWidget** (`src/gui/search_widget.py`)
   - User interface for search functionality
   - Advanced filtering options
   - Search history and saved searches management

3. **Database Integration**
   - FTS5 virtual tables synchronized with main data tables
   - Automatic triggers to keep search indexes up-to-date

## Features

### Full-Text Search

The search engine uses SQLite FTS5 for fast full-text search across:
- Model titles
- Descriptions
- Keywords
- Filenames
- Categories
- Sources

#### Boolean Operators

Support for advanced search queries with boolean operators:
- `AND` - Intersection of terms
- `OR` - Union of terms
- `NOT` - Exclusion of terms
- Parentheses for grouping
- Exact phrases in quotes

Example queries:
```
character AND fantasy
building OR architecture
vehicle NOT car
"medieval castle" AND (building OR architecture)
```

### Filtering Options

#### Category Filtering
Filter by one or more categories:
- Characters
- Buildings
- Vehicles
- Nature
- Objects
- Abstract
- Other

#### Format Filtering
Filter by file format:
- STL
- OBJ
- 3MF
- STEP

#### Rating Filtering
Filter by minimum rating (1-5 stars).

#### Date Range Filtering
Filter by date added or last viewed:
- Date added start/end
- Last viewed start/end

#### File Size Filtering
Filter by file size in megabytes:
- Minimum file size
- Maximum file size

### Search History

The search engine maintains a history of recent searches:
- Automatic recording of all searches
- Timestamp for each search
- Query and filters saved
- Quick access to previous searches
- Configurable history retention period

### Saved Searches

Users can save frequently used searches:
- Custom names for saved searches
- Complete search criteria saved
- Quick access to complex searches
- Management of saved searches

### Search Suggestions

As-you-type search suggestions:
- Based on existing content
- Fast response with minimal UI impact
- Helps users discover relevant content

## Implementation Details

### FTS5 Virtual Tables

The search engine creates two FTS5 virtual tables:

#### models_fts
```sql
CREATE VIRTUAL TABLE models_fts USING fts5(
    filename,
    format,
    file_path,
    content='models',
    content_rowid='id'
);
```

#### model_metadata_fts
```sql
CREATE VIRTUAL TABLE model_metadata_fts USING fts5(
    title,
    description,
    keywords,
    category,
    source,
    content='model_metadata',
    content_rowid='model_id'
);
```

### Triggers

Automatic triggers keep FTS tables synchronized:

```sql
CREATE TRIGGER models_ai AFTER INSERT ON models BEGIN
    INSERT INTO models_fts(rowid, filename, format, file_path)
    VALUES (new.id, new.filename, new.format, new.file_path);
END;
```

Similar triggers exist for UPDATE and DELETE operations on both tables.

### Search Query Building

The search engine dynamically builds SQL queries based on search criteria:

```sql
SELECT 
    m.*, mm.title, mm.description, mm.keywords, mm.category,
    mm.source, mm.rating, mm.view_count, mm.last_viewed,
    bm25(models_fts) + bm25(model_metadata_fts) as rank
FROM models m
LEFT JOIN model_metadata mm ON m.id = mm.model_id
LEFT JOIN models_fts ON m.id = models_fts.rowid
LEFT JOIN model_metadata_fts ON mm.model_id = model_metadata_fts.rowid
WHERE (models_fts MATCH ? OR model_metadata_fts MATCH ?)
AND mm.category = ?
AND m.format = ?
ORDER BY rank DESC, last_viewed DESC
```

### Performance Optimization

#### BM25 Ranking
Uses BM25 algorithm for relevance ranking:
- Considers term frequency
- Accounts for document length
- Provides relevance scores

#### Query Optimization
- Efficient use of indexes
- Proper query planning
- Minimal database round trips

#### Caching
- Query result caching for common searches
- In-memory caching of frequently accessed data

## Usage Examples

### Basic Search

```python
from src.core.search_engine import get_search_engine

# Get search engine instance
search_engine = get_search_engine()

# Perform simple text search
results = search_engine.search("character")

# Process results
for model in results["results"]:
    print(f"Found: {model['title']} (ID: {model['id']})")
```

### Advanced Search with Filters

```python
# Search with filters
filters = {
    "category": ["Characters", "Buildings"],
    "format": "stl",
    "min_rating": 4,
    "date_added_start": "2023-01-01"
}

results = search_engine.search("fantasy", filters)
```

### Search Suggestions

```python
# Get search suggestions
suggestions = search_engine.get_search_suggestions("cha")
print(suggestions)  # ["character", "character model", ...]
```

### Saved Searches

```python
# Save a search
search_id = search_engine.save_search(
    name="My Character Search",
    query="character",
    filters={"category": "Characters", "min_rating": 4}
)

# Get all saved searches
saved_searches = search_engine.get_saved_searches()

# Delete a saved search
search_engine.delete_saved_search(search_id)
```

## Performance Metrics

### Search Response Times
- Target: < 1 second for metadata search
- Typical: 100-300ms for most queries
- Large collections: < 500ms with proper indexing

### Memory Usage
- Efficient memory management
- No memory leaks during repeated operations
- Adaptive memory allocation based on available RAM

### Scalability
- Tested with 10,000+ models
- Linear performance degradation
- Suitable for large collections

## Troubleshooting

### Common Issues

#### Slow Search Performance
1. Check if FTS indexes are up-to-date
2. Rebuild FTS indexes if necessary
3. Verify database optimization settings

```python
# Rebuild FTS indexes
search_engine.rebuild_fts_indexes()

# Optimize database
search_engine.db_manager.analyze_database()
```

#### Missing Search Results
1. Verify FTS triggers are working
2. Check if content is properly indexed
3. Rebuild FTS tables

#### Search Suggestions Not Working
1. Check if content is indexed
2. Verify minimum query length (2 characters)
3. Check for special characters in query

### Debug Mode

Enable debug logging for detailed search information:

```python
import logging
logging.getLogger('src.core.search_engine').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **Fuzzy Search**: Support for typo-tolerant searching
2. **Semantic Search**: AI-powered semantic understanding
3. **Faceted Search**: Enhanced filtering with facet counts
4. **Search Analytics**: Usage statistics and popular searches
5. **Collaborative Filtering**: Recommendation based on usage patterns

### Performance Improvements
1. **Incremental Updates**: More efficient FTS updates
2. **Parallel Processing**: Multi-threaded search operations
3. **Query Caching**: Enhanced caching strategies
4. **Index Optimization**: Advanced FTS configuration

## API Reference

### SearchEngine Class

#### Methods

##### `search(query, filters=None, limit=100, offset=0)`
Perform a search with optional filters.

**Parameters:**
- `query` (str): Search query string
- `filters` (dict, optional): Filter criteria
- `limit` (int): Maximum number of results
- `offset` (int): Number of results to skip

**Returns:**
- `dict`: Search results with metadata

##### `get_search_suggestions(query, limit=10)`
Get search suggestions for partial query.

**Parameters:**
- `query` (str): Partial search query
- `limit` (int): Maximum number of suggestions

**Returns:**
- `list`: List of suggestion strings

##### `save_search(name, query, filters)`
Save a search with custom name.

**Parameters:**
- `name` (str): Name for the saved search
- `query` (str): Search query
- `filters` (dict): Search filters

**Returns:**
- `int`: ID of the saved search

##### `get_saved_searches()`
Get all saved searches.

**Returns:**
- `list`: List of saved search dictionaries

##### `delete_saved_search(search_id)`
Delete a saved search.

**Parameters:**
- `search_id` (int): ID of the saved search

**Returns:**
- `bool`: True if successful

##### `get_search_history(limit=50)`
Get recent search history.

**Parameters:**
- `limit` (int): Maximum number of history items

**Returns:**
- `list`: List of search history items

##### `clear_search_history(older_than_days=30)`
Clear old search history.

**Parameters:**
- `older_than_days` (int): Clear history older than this many days

**Returns:**
- `int`: Number of records deleted

##### `rebuild_fts_indexes()`
Rebuild FTS indexes from scratch.

**Note:** This operation can be time-consuming for large databases.

## Testing

### Running Tests

```bash
# Run all search engine tests
python -m pytest tests/test_search_engine.py

# Run specific test
python -m pytest tests/test_search_engine.py::TestSearchEngine::test_basic_search

# Run with verbose output
python -m pytest tests/test_search_engine.py -v
```

### Test Coverage

The test suite covers:
- Basic search functionality
- Advanced filtering
- Boolean operators
- Search history
- Saved searches
- Performance benchmarks
- Edge cases and error handling

### Performance Testing

Run performance tests to verify search response times:

```python
# Test search performance
python tests/performance/search_performance_test.py
```

## Conclusion

The 3D-MM search engine provides a robust, efficient solution for finding 3D models in large collections. With FTS5 technology, advanced filtering, and comprehensive search management features, users can quickly locate the models they need.

The implementation follows best practices for performance, memory management, and user experience, making it suitable for both small personal collections and large professional libraries.
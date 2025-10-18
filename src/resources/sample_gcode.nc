; Sample G-code file for testing G-code Previewer
; Simple rectangular pocket with rounded corners

G90 ; Absolute positioning
G21 ; Metric units
G17 ; XY plane

; Tool change
T1 M6 ; Select tool 1
M3 S1200 ; Spindle on, 1200 RPM

; Rapid to start position
G00 X10.0 Y10.0 Z5.0

; Plunge to depth
G01 Z-5.0 F100

; First side - bottom edge
G01 X100.0 Y10.0 F200
G01 X100.0 Y100.0 F200
G01 X10.0 Y100.0 F200
G01 X10.0 Y10.0 F200

; Rapid to next level
G00 Z5.0

; Second pass - deeper
G01 Z-10.0 F100
G01 X100.0 Y10.0 F200
G01 X100.0 Y100.0 F200
G01 X10.0 Y100.0 F200
G01 X10.0 Y10.0 F200

; Rapid to clearance
G00 Z20.0

; Rapid to home
G00 X0.0 Y0.0 Z0.0

; Spindle off
M5

; Program end
M30


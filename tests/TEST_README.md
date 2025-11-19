# Testing HeightOfTerrain.py

This directory contains comprehensive unit and property-based tests for the HeightOfTerrain script using pytest and Hypothesis.

## Installation

Install the test dependencies:

```bash
pip install -r test_requirements.txt
```

## Running Tests

### Run all tests:
```bash
pytest test_HeightOfTerrain.py
```

### Run with verbose output:
```bash
pytest test_HeightOfTerrain.py -v
```

### Run with coverage report:
```bash
pytest test_HeightOfTerrain.py --cov=HeightOfTerrain --cov-report=html
```

### Run specific test classes:
```bash
# Run only unit tests for datetoday
pytest test_HeightOfTerrain.py::TestDatetoday -v

# Run only HeightOfTerrain function tests
pytest test_HeightOfTerrain.py::TestHeightOfTerrain -v

# Run only property-based tests
pytest test_HeightOfTerrain.py::TestPropertyBased -v

# Run only integration tests
pytest test_HeightOfTerrain.py::TestIntegration -v

# Run only edge case tests
pytest test_HeightOfTerrain.py::TestEdgeCases -v
```

### Run specific test methods:
```bash
pytest test_HeightOfTerrain.py::TestDatetoday::test_datetoday_format -v
```

## Test Structure

### 1. Unit Tests

#### TestDatetoday
- `test_datetoday_format`: Verifies the date string format
- `test_datetoday_valid_month`: Checks month name validity
- `test_datetoday_current_year`: Confirms correct year
- `test_datetoday_mocked_date`: Tests with mocked datetime

#### TestHeightOfTerrain
- `test_height_of_terrain_nan_lat`: Tests NaN latitude handling
- `test_height_of_terrain_nan_lon`: Tests NaN longitude handling
- `test_height_of_terrain_both_nan`: Tests both coordinates as NaN
- `test_height_of_terrain_missing_file`: Tests missing terrain data
- `test_height_of_terrain_north_west`: Tests northern/western coordinates
- `test_height_of_terrain_south_east`: Tests southern/eastern coordinates
- `test_height_of_terrain_invalid_value_replacement`: Tests -32768 to NaN conversion
- `test_height_of_terrain_indexing`: Tests array indexing logic
- `test_height_of_terrain_boundary_lat`: Tests integer latitude boundary

#### TestParseArgs
- `test_parse_args_defaults`: Tests default argument values
- `test_parse_args_custom_values`: Tests custom command-line arguments

### 2. Property-Based Tests (Hypothesis)

#### TestPropertyBased
- `test_latitude_range_valid`: Tests all valid latitudes (-90 to 90)
- `test_longitude_range_valid`: Tests all valid longitudes (-180 to 180)
- `test_height_return_type`: Verifies return type consistency
- `test_nan_lat_always_returns_nan`: Property: NaN input → NaN output
- `test_nan_lon_always_returns_nan`: Property: NaN input → NaN output
- `test_hemisphere_naming_consistency`: Verifies N/S/E/W naming logic
- `test_integer_coordinates`: Tests integer coordinate handling
- `test_batch_coordinates`: Tests batch processing with random coordinate arrays

### 3. Integration Tests

#### TestIntegration
- `test_file_naming_convention`: Tests terrain file naming across different coordinates
- Uses `mock_netcdf_file` fixture for NetCDF integration testing

### 4. Edge Case Tests

#### TestEdgeCases
- `test_equator_crossing`: Tests coordinates at equator
- `test_prime_meridian_crossing`: Tests coordinates at 0° longitude
- `test_dateline_crossing`: Tests coordinates near ±180° longitude
- `test_poles`: Tests coordinates near poles
- `test_very_small_decimal_values`: Tests precision handling
- `test_very_large_decimal_values`: Tests boundary decimal values

## Test Coverage

The test suite covers:
- ✓ Basic functionality of all public functions
- ✓ Edge cases and boundary conditions
- ✓ Error handling (NaN values, missing files)
- ✓ File I/O operations (with mocking)
- ✓ Coordinate system conversions (hemispheres)
- ✓ Data type handling and conversions
- ✓ Property-based testing for wide input ranges
- ✓ Integration with external dependencies (NetCDF, numpy arrays)

## Notes

### Fixtures
- `temp_terrain_data`: Creates temporary terrain data directory with sample .hgt files
- `mock_netcdf_file`: Creates mock NetCDF file for integration testing

### Mocking
The tests use mocking to avoid:
- Downloading actual terrain data
- Creating large test files
- Depending on external network resources

### Property-Based Testing
Hypothesis is used to automatically generate test cases covering:
- Wide ranges of latitude/longitude values
- Edge cases near boundaries
- Random coordinate arrays for batch testing
- NaN and special value handling
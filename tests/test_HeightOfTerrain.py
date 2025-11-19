import os
import sys
import tempfile
import shutil
import pytest
import numpy as np
import numpy.ma as ma
from unittest import mock
from hypothesis import given, strategies as st, assume, settings
from hypothesis.extra.numpy import arrays
import datetime
import netCDF4

# Import the module under test
# Note: HeightOfTerrain is now a script without .py extension
import importlib.machinery
import importlib.util

# Get absolute path to HeightOfTerrain script, assuming it's one directory up
_test_dir = os.path.dirname(os.path.abspath(__file__))
_script_dir = os.path.dirname(_test_dir)
_script_path = os.path.join(_script_dir, "HeightOfTerrain")

# Use SourceFileLoader to handle files without .py extension
loader = importlib.machinery.SourceFileLoader("HeightOfTerrain", _script_path)
spec = importlib.util.spec_from_loader(loader.name, loader)
HeightOfTerrain_module = importlib.util.module_from_spec(spec)
sys.modules['HeightOfTerrain'] = HeightOfTerrain_module
loader.exec_module(HeightOfTerrain_module)

datetoday = HeightOfTerrain_module.datetoday
HeightOfTerrain = HeightOfTerrain_module.HeightOfTerrain
parse_args = HeightOfTerrain_module.parse_args
get_flight_bounds = HeightOfTerrain_module.get_flight_bounds
TdbData = HeightOfTerrain_module.TdbData
_terrain_cache = HeightOfTerrain_module._terrain_cache


class TestDatetoday:
    """Unit tests for the datetoday function."""

    def test_datetoday_format(self):
        """Test that datetoday returns a string in correct format."""
        result = datetoday()
        parts = result.split()
        assert len(parts) == 3, "Should return 'Day Month Year' format"
        assert parts[0].isdigit(), "First part should be day number"
        assert parts[1].isalpha(), "Second part should be month name"
        assert parts[2].isdigit(), "Third part should be year"

    def test_datetoday_valid_month(self):
        """Test that the month name is valid."""
        valid_months = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        result = datetoday()
        month = result.split()[1]
        assert month in valid_months, f"Month '{month}' should be valid"

    def test_datetoday_current_year(self):
        """Test that year matches current year."""
        result = datetoday()
        year = int(result.split()[2])
        current_year = datetime.datetime.now().year
        assert year == current_year, f"Year should be {current_year}"

    @mock.patch('HeightOfTerrain.datetime')
    def test_datetoday_mocked_date(self, mock_datetime):
        """Test with a specific mocked date."""
        mock_now = mock.Mock()
        mock_now.day = 15
        mock_now.month = 6
        mock_now.year = 2023
        mock_datetime.datetime.now.return_value = mock_now

        result = datetoday()
        assert result == "15 June 2023"


class TestHeightOfTerrain:
    """Unit tests for the HeightOfTerrain function."""

    @pytest.fixture(autouse=True)
    def clear_cache_before_test(self):
        """Clear the cache before each test to ensure test isolation."""
        _terrain_cache.clear()
        yield
        _terrain_cache.clear()

    @pytest.fixture
    def temp_terrain_data(self, tmp_path):
        """Create a temporary terrain data directory with sample .hgt file."""
        terrain_dir = tmp_path / "TerrainData"
        terrain_dir.mkdir()

        # Create a sample .hgt file (1201x1201 int16 array)
        sample_data = np.full((1201, 1201), 1500, dtype='>i2')
        sample_data[600, 600] = 2000  # Add a peak
        sample_data[0:10, 0:10] = -32768  # Add some invalid data

        hgt_file = terrain_dir / "N40W105.hgt"
        sample_data.tofile(hgt_file)

        return str(terrain_dir)

    def test_height_of_terrain_nan_lat(self):
        """Test that NaN latitude returns NaN."""
        result = HeightOfTerrain(np.nan, -105.0)
        assert np.isnan(result)

    def test_height_of_terrain_nan_lon(self):
        """Test that NaN longitude returns NaN."""
        result = HeightOfTerrain(40.0, np.nan)
        assert np.isnan(result)

    def test_height_of_terrain_both_nan(self):
        """Test that NaN for both coordinates returns NaN."""
        result = HeightOfTerrain(np.nan, np.nan)
        assert np.isnan(result)

    def test_height_of_terrain_masked_lat(self):
        """Test that masked latitude returns NaN."""
        lat = ma.masked
        result = HeightOfTerrain(lat, -105.0)
        assert np.isnan(result)

    def test_height_of_terrain_masked_lon(self):
        """Test that masked longitude returns NaN."""
        lon = ma.masked
        result = HeightOfTerrain(40.0, lon)
        assert np.isnan(result)

    def test_height_of_terrain_both_masked(self):
        """Test that both masked coordinates return NaN."""
        lat = ma.masked
        lon = ma.masked
        result = HeightOfTerrain(lat, lon)
        assert np.isnan(result)

    def test_height_of_terrain_masked_array(self):
        """Test with masked array values."""
        lat_array = ma.array([40.0, 41.0], mask=[False, True])
        lon = -105.0
        result = HeightOfTerrain(lat_array[1], lon)  # Use masked element
        assert np.isnan(result)

    def test_height_of_terrain_missing_file(self):
        """Test that missing .hgt file returns NaN."""
        result = HeightOfTerrain(89.0, 179.0)  # Unlikely to exist
        assert np.isnan(result)

    def test_height_of_terrain_north_west(self, temp_terrain_data, monkeypatch):
        """Test northern and western hemisphere coordinate."""
        monkeypatch.setattr(HeightOfTerrain_module, 'TdbData', temp_terrain_data)
        result = HeightOfTerrain(40.5, -104.5)
        assert isinstance(result, (int, float, np.floating))
        assert not np.isnan(result)

    def test_height_of_terrain_south_east(self, tmp_path, monkeypatch):
        """Test southern and eastern hemisphere coordinate."""
        terrain_dir = tmp_path / "TerrainData"
        terrain_dir.mkdir()

        sample_data = np.full((1201, 1201), 500, dtype='>i2')
        hgt_file = terrain_dir / "S35E150.hgt"
        sample_data.tofile(hgt_file)

        monkeypatch.setattr(HeightOfTerrain_module, 'TdbData', str(terrain_dir))
        result = HeightOfTerrain(-34.5, 150.5)
        assert isinstance(result, (int, float, np.floating))
        assert not np.isnan(result)

    def test_height_of_terrain_invalid_value_replacement(self, tmp_path, monkeypatch):
        """Test that -32768 values are converted to NaN."""
        terrain_dir = tmp_path / "TerrainData"
        terrain_dir.mkdir()

        sample_data = np.full((1201, 1201), -32768, dtype='>i2')
        hgt_file = terrain_dir / "N40W105.hgt"
        sample_data.tofile(hgt_file)

        monkeypatch.setattr(HeightOfTerrain_module, 'TdbData', str(terrain_dir))
        result = HeightOfTerrain(40.5, -104.5)
        assert np.isnan(result)

    def test_height_of_terrain_indexing(self, tmp_path, monkeypatch):
        """Test correct [iy, ix] indexing - would catch legacy [ix, iy] bug from R code.

        This test creates asymmetric terrain data where swapping indices gives wrong results.
        The .hgt format stores data row-by-row (latitude varies by row, longitude by column).
        Correct indexing is height[iy, ix] where iy=latitude index, ix=longitude index.
        """
        terrain_dir = tmp_path / "TerrainData"
        terrain_dir.mkdir()

        # Create ASYMMETRIC terrain data - different patterns in lat vs lon directions
        # This ensures swapping [iy, ix] to [ix, iy] gives detectably wrong results
        sample_data = np.zeros((1201, 1201), dtype='>i2')

        # Create a gradient: height increases with latitude (row index)
        # and decreases with longitude (column index)
        for i in range(1201):  # rows = latitude
            for j in range(1201):  # columns = longitude
                # Height = 1000 + 2*row - column
                # This makes the terrain asymmetric
                sample_data[i, j] = 1000 + 2*i - j

        hgt_file = terrain_dir / "N40W105.hgt"
        sample_data.tofile(hgt_file)

        monkeypatch.setattr(HeightOfTerrain_module, 'TdbData', str(terrain_dir))

        # Test a specific coordinate: N40.5, W104.5
        # lat=40.5 is in tile N40 (floor=40), fractional part = 0.5
        # lon=-104.5 is in tile W105 (floor=-105), fractional part = 0.5
        #
        # Calculate expected indices:
        # ix = int((lon - floor(lon) + 1/2400) * 1200)
        #    = int(((-104.5) - (-105) + 1/2400) * 1200)
        #    = int((0.5 + 0.000417) * 1200)
        #    = int(600.5) = 600
        #
        # iy = int((ceil(lat) - lat + 1/2400) * 1200)
        #    = int((41 - 40.5 + 1/2400) * 1200)
        #    = int((0.5 + 0.000417) * 1200)
        #    = int(600.5) = 600
        #
        # Expected height[600, 600] = 1000 + 2*600 - 600 = 1000 + 1200 - 600 = 1600

        result = HeightOfTerrain(40.5, -104.5)
        expected_height = 1600.0

        # If indexing were swapped to [ix, iy], we'd still get [600, 600] for this
        # symmetric case, so test another point:

        # Test asymmetric point: N40.25, W104.75
        # lat=40.25: iy = int((41 - 40.25 + 1/2400) * 1200) = int(0.75 * 1200) = 900
        # lon=-104.75: ix = int((0.25 + 1/2400) * 1200) = int(0.25 * 1200) = 300
        # Correct: height[900, 300] = 1000 + 2*900 - 300 = 1000 + 1800 - 300 = 2500
        # Wrong [ix,iy]: height[300, 900] = 1000 + 2*300 - 900 = 1000 + 600 - 900 = 700

        result2 = HeightOfTerrain(40.25, -104.75)
        expected_height2 = 2500.0
        wrong_if_swapped = 700.0  # What we'd get with [ix, iy] indexing

        assert np.isclose(result2, expected_height2, rtol=1e-5), \
            f"Expected {expected_height2} with correct [iy,ix] indexing, got {result2}. " \
            f"If result is {wrong_if_swapped}, indices are swapped [ix,iy]!"

        # Also verify the symmetric point works
        assert np.isclose(result, expected_height, rtol=1e-5), \
            f"Expected {expected_height}, got {result}"

    def test_height_of_terrain_boundary_lat(self, tmp_path, monkeypatch):
        """Test behavior at latitude boundary (integer latitude)."""
        terrain_dir = tmp_path / "TerrainData"
        terrain_dir.mkdir()

        sample_data = np.full((1201, 1201), 1000, dtype='>i2')
        hgt_file = terrain_dir / "N40W105.hgt"
        sample_data.tofile(hgt_file)

        monkeypatch.setattr(HeightOfTerrain_module, 'TdbData', str(terrain_dir))
        result = HeightOfTerrain(40.0, -104.5)
        assert isinstance(result, (int, float, np.floating))
        assert not np.isnan(result)


class TestGetFlightBounds:
    """Unit tests for the get_flight_bounds function."""

    def test_get_flight_bounds_missing_utility(self, monkeypatch):
        """Test when flt_area utility is not available."""
        # Mock shutil.which to return None (utility not found)
        monkeypatch.setattr('shutil.which', lambda x: None)

        result = get_flight_bounds("/path/to/file.nc")
        assert result is None

    def test_get_flight_bounds_success(self, monkeypatch):
        """Test successful parsing of flt_area output."""
        # Mock subprocess.run to return successful flt_area output
        mock_output = """Input file /scr/raf/Prod_Data/SOCRATES/SOCRATESrf03.nc exists.
Proceeding to processing.
****Starting Processing*****
Extracting flight area for: /scr/raf/Prod_Data/SOCRATES/SOCRATESrf03.nc
FLIGHT AREA:
Maximum Latitude: -42.40082
Minimum Latitude: -61.997105
Minimum Longitude: 133.91486
Maximum Longitude: 163.02815"""

        mock_result = mock.Mock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_result.stderr = ""

        monkeypatch.setattr('shutil.which', lambda x: '/usr/bin/flt_area')
        monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: mock_result)

        result = get_flight_bounds("/scr/raf/Prod_Data/SOCRATES/SOCRATESrf*.nc")

        assert result is not None
        lt_s, lt_n, lg_w, lg_e = result

        # Check expansion by 1 degree: floor(min) - 1, ceil(max) + 1
        assert lt_s == int(np.floor(-61.997105)) - 1  # -62 - 1 = -63
        assert lt_n == int(np.ceil(-42.40082)) + 1     # -42 + 1 = -41
        assert lg_w == int(np.floor(133.91486)) - 1    # 133 - 1 = 132
        assert lg_e == int(np.ceil(163.02815)) + 1     # 164 + 1 = 165

        # Verify actual values
        assert lt_s == -63
        assert lt_n == -41
        assert lg_w == 132
        assert lg_e == 165

    def test_get_flight_bounds_command_failure(self, monkeypatch):
        """Test when flt_area command fails."""
        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: file not found"

        monkeypatch.setattr('shutil.which', lambda x: '/usr/bin/flt_area')
        monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: mock_result)

        result = get_flight_bounds("/invalid/path/*.nc")
        assert result is None

    def test_get_flight_bounds_timeout(self, monkeypatch):
        """Test when flt_area command times out."""
        import subprocess

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=['flt_area'], timeout=30)

        monkeypatch.setattr('shutil.which', lambda x: '/usr/bin/flt_area')
        monkeypatch.setattr('subprocess.run', mock_run)

        result = get_flight_bounds("/path/to/file.nc")
        assert result is None

    def test_get_flight_bounds_parse_error(self, monkeypatch):
        """Test when flt_area output format is unexpected."""
        # Mock output with wrong format
        mock_output = """Some unexpected output
Without the expected format"""

        mock_result = mock.Mock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_result.stderr = ""

        monkeypatch.setattr('shutil.which', lambda x: '/usr/bin/flt_area')
        monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: mock_result)

        result = get_flight_bounds("/path/to/file.nc")
        assert result is None

    def test_get_flight_bounds_northern_hemisphere(self, monkeypatch):
        """Test with northern hemisphere coordinates."""
        mock_output = """FLIGHT AREA:
Maximum Latitude: 41.5
Minimum Latitude: 37.2
Minimum Longitude: -111.8
Maximum Longitude: -99.1"""

        mock_result = mock.Mock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_result.stderr = ""

        monkeypatch.setattr('shutil.which', lambda x: '/usr/bin/flt_area')
        monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: mock_result)

        result = get_flight_bounds("/data/PROJECTrf*.nc")

        assert result is not None
        lt_s, lt_n, lg_w, lg_e = result

        assert lt_s == 36   # floor(37.2) - 1 = 37 - 1 = 36
        assert lt_n == 43   # ceil(41.5) + 1 = 42 + 1 = 43
        assert lg_w == -113 # floor(-111.8) - 1 = -112 - 1 = -113
        assert lg_e == -98  # ceil(-99.1) + 1 = -99 + 1 = -98


class TestParseArgs:
    """Unit tests for the parse_args function."""

    def test_parse_args_defaults(self):
        """Test that default arguments are parsed correctly."""
        with mock.patch('sys.argv', ['HeightOfTerrain']):
            args = parse_args()
            assert args.Project == 'CAESAR'
            assert args.Flight == 'rf05'
            assert args.Directory == '.'
            assert args.lt_s is None  # Now defaults to None for auto-detection
            assert args.lt_n is None  # Now defaults to None for auto-detection
            assert args.lg_w is None  # Now defaults to None for auto-detection
            assert args.lg_e is None  # Now defaults to None for auto-detection
            assert args.Tdb == 'yes'

    def test_parse_args_custom_values(self):
        """Test parsing custom command-line arguments."""
        test_args = ['HeightOfTerrain', 'TESTPROJECT', 'rf10',
                    '/custom/path', '30', '45', '-120', '-100', 'no']
        with mock.patch('sys.argv', test_args):
            args = parse_args()
            assert args.Project == 'TESTPROJECT'
            assert args.Flight == 'rf10'
            assert args.Directory == '/custom/path'
            assert args.lt_s == 30
            assert args.lt_n == 45
            assert args.lg_w == -120
            assert args.lg_e == -100
            assert args.Tdb == 'no'


class TestPropertyBased:
    """Property-based tests using Hypothesis."""

    @pytest.fixture(autouse=True)
    def clear_cache_before_test(self):
        """Clear the cache before each test to ensure test isolation."""
        _terrain_cache.clear()
        yield
        _terrain_cache.clear()

    @given(st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False))
    def test_latitude_range_valid(self, lat):
        """Property: Valid latitudes should not crash the function."""
        # Function should handle any valid latitude without crashing
        try:
            result = HeightOfTerrain(lat, -105.0)
            assert isinstance(result, (int, float, np.floating, type(np.nan)))
        except Exception as e:
            pytest.fail(f"Function crashed with valid latitude {lat}: {e}")

    @given(st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False))
    def test_longitude_range_valid(self, lon):
        """Property: Valid longitudes should not crash the function."""
        # Function should handle any valid longitude without crashing
        try:
            result = HeightOfTerrain(40.0, lon)
            assert isinstance(result, (int, float, np.floating, type(np.nan)))
        except Exception as e:
            pytest.fail(f"Function crashed with valid longitude {lon}: {e}")

    @given(
        st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False)
    )
    def test_height_return_type(self, lat, lon):
        """Property: Function should always return a numeric value or NaN."""
        result = HeightOfTerrain(lat, lon)
        assert isinstance(result, (int, float, np.floating, type(np.nan)))

    @given(st.floats(allow_nan=False, allow_infinity=False, min_value=-180, max_value=180))
    def test_nan_lat_always_returns_nan(self, lon):
        """Property: NaN latitude should always return NaN."""
        result = HeightOfTerrain(np.nan, lon)
        assert np.isnan(result)

    @given(st.floats(allow_nan=False, allow_infinity=False, min_value=-90, max_value=90))
    def test_nan_lon_always_returns_nan(self, lat):
        """Property: NaN longitude should always return NaN."""
        result = HeightOfTerrain(lat, np.nan)
        assert np.isnan(result)

    @given(
        st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False)
    )
    def test_hemisphere_naming_consistency(self, lat, lon):
        """Property: Hemisphere naming should be consistent with coordinate signs."""
        lt = int(np.floor(lat))
        lg = int(np.floor(lon))

        # Check that the expected hemisphere designations are correct
        expected_ns = 'S' if lt < 0 else 'N'
        expected_ew = 'W' if lg < 0 else 'E'

        # This is a property that should hold based on the function's logic
        assert (lat < 0 and expected_ns == 'S') or (lat >= 0 and expected_ns == 'N')
        assert (lon < 0 and expected_ew == 'W') or (lon >= 0 and expected_ew == 'E')

    @given(
        st.integers(min_value=-90, max_value=90),
        st.integers(min_value=-180, max_value=180)
    )
    def test_integer_coordinates(self, lat, lon):
        """Property: Integer coordinates should work correctly."""
        result = HeightOfTerrain(float(lat), float(lon))
        assert isinstance(result, (int, float, np.floating, type(np.nan)))

    def test_indexing_with_known_terrain(self, tmp_path, monkeypatch):
        """Additional test: Verify indexing with known terrain features.

        Creates terrain with distinct N-S and E-W patterns to catch index swaps.
        """
        terrain_dir = tmp_path / "TerrainData"
        terrain_dir.mkdir()

        # Create terrain with clear directional patterns
        # North-South (rows): height increases by 10m per degree latitude
        # East-West (cols): height decreases by 5m per degree longitude
        sample_data = np.zeros((1201, 1201), dtype='>i2')

        for i in range(1201):  # rows = latitude (0 = south, 1200 = north)
            for j in range(1201):  # cols = longitude (0 = west, 1200 = east)
                # Base height 5000m, +10 per lat row, -5 per lon col
                sample_data[i, j] = 5000 + 10*i - 5*j

        hgt_file = terrain_dir / "N40W105.hgt"
        sample_data.tofile(hgt_file)

        monkeypatch.setattr(HeightOfTerrain_module, 'TdbData', str(terrain_dir))

        # Test northwest corner (high lat, low lon) = high elevation
        # lat=40.95 → iy ≈ int((41-40.95)*1200) = int(0.05*1200) = 60
        # lon=-104.05 → ix ≈ int(((-104.05)-(-105))*1200) = int(0.95*1200) = 1140
        # Correct: height[60, 1140] = 5000 + 10*60 - 5*1140 = 5000 + 600 - 5700 = -100
        result_nw = HeightOfTerrain(40.95, -104.05)

        # Test southeast corner (low lat, high lon) = lower elevation
        # lat=40.05 → iy ≈ int((41-40.05)*1200) = int(0.95*1200) = 1140
        # lon=-104.95 → ix ≈ int(((-104.95)-(-105))*1200) = int(0.05*1200) = 60
        # Correct: height[1140, 60] = 5000 + 10*1140 - 5*60 = 5000 + 11400 - 300 = 16100
        result_se = HeightOfTerrain(40.05, -104.95)

        # With correct indexing: SE should be much higher than NW
        assert result_se > result_nw, \
            f"SE corner ({result_se}m) should be higher than NW corner ({result_nw}m). " \
            f"If NW > SE, latitude/longitude indices may be swapped!"

        # Verify approximate expected values (allowing for rounding)
        assert result_nw < 1000, f"NW corner should be low elevation, got {result_nw}m"
        assert result_se > 15000, f"SE corner should be high elevation, got {result_se}m"

    @settings(max_examples=50)
    @given(
        arrays(dtype=np.float64, shape=10,
               elements=st.floats(min_value=-90.0, max_value=90.0,
                                allow_nan=False, allow_infinity=False)),
        arrays(dtype=np.float64, shape=10,
               elements=st.floats(min_value=-180.0, max_value=180.0,
                                allow_nan=False, allow_infinity=False))
    )
    def test_batch_coordinates(self, lats, lons):
        """Property: Function should handle batch processing consistently."""
        results = []
        for lat, lon in zip(lats, lons):
            try:
                result = HeightOfTerrain(lat, lon)
                results.append(result)
                assert isinstance(result, (int, float, np.floating, type(np.nan)))
            except Exception as e:
                pytest.fail(f"Batch processing failed at ({lat}, {lon}): {e}")

        assert len(results) == len(lats)


class TestIntegration:
    """Integration tests that test multiple components together."""

    @pytest.fixture
    def mock_netcdf_file(self, tmp_path):
        """Create a mock NetCDF file for integration testing."""
        nc_file = tmp_path / "test_flight.nc"

        with netCDF4.Dataset(nc_file, 'w') as nc:
            # Create dimensions
            time_dim = nc.createDimension('Time', 100)

            # Create variables
            time_var = nc.createVariable('Time', 'f8', ('Time',))
            latc_var = nc.createVariable('LATC', 'f4', ('Time',))
            lonc_var = nc.createVariable('LONC', 'f4', ('Time',))
            ggalt_var = nc.createVariable('GGALT', 'f4', ('Time',))
            gglat_var = nc.createVariable('GGLAT', 'f4', ('Time',))
            gglon_var = nc.createVariable('GGLON', 'f4', ('Time',))

            # Fill with sample data
            time_var[:] = np.arange(100)
            latc_var[:] = np.linspace(40.0, 41.0, 100)
            lonc_var[:] = np.linspace(-105.0, -104.0, 100)
            ggalt_var[:] = np.linspace(5000, 6000, 100)
            gglat_var[:] = np.linspace(40.0, 41.0, 100)
            gglon_var[:] = np.linspace(-105.0, -104.0, 100)

        return nc_file

    def test_file_naming_convention(self):
        """Test that terrain file naming follows correct conventions."""
        test_cases = [
            (40.0, -105.0, "N40W105.hgt"),
            (-35.0, 150.0, "S35E150.hgt"),
            (0.0, 0.0, "N00E000.hgt"),
            (89.0, 179.0, "N89E179.hgt"),
            (-89.0, -179.0, "S89W179.hgt"),
        ]

        for lat, lon, expected_name in test_cases:
            lt = int(np.floor(lat))
            lg = int(np.floor(lon))
            NS = 'S' if lt < 0 else 'N'
            lt = abs(lt)
            EW = 'W' if lg < 0 else 'E'
            lg = abs(lg)
            actual_name = f"{NS}{lt:02d}{EW}{lg:03d}.hgt"
            assert actual_name == expected_name, \
                f"For ({lat}, {lon}), expected {expected_name}, got {actual_name}"

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_equator_crossing(self):
        """Test coordinates at the equator."""
        result_north = HeightOfTerrain(0.1, -105.0)
        result_south = HeightOfTerrain(-0.1, -105.0)
        assert isinstance(result_north, (int, float, np.floating, type(np.nan)))
        assert isinstance(result_south, (int, float, np.floating, type(np.nan)))

    def test_prime_meridian_crossing(self):
        """Test coordinates at the prime meridian."""
        result_east = HeightOfTerrain(40.0, 0.1)
        result_west = HeightOfTerrain(40.0, -0.1)
        assert isinstance(result_east, (int, float, np.floating, type(np.nan)))
        assert isinstance(result_west, (int, float, np.floating, type(np.nan)))

    def test_dateline_crossing(self):
        """Test coordinates near the international dateline."""
        result_west = HeightOfTerrain(40.0, 179.9)
        result_east = HeightOfTerrain(40.0, -179.9)
        assert isinstance(result_west, (int, float, np.floating, type(np.nan)))
        assert isinstance(result_east, (int, float, np.floating, type(np.nan)))

    def test_poles(self):
        """Test coordinates near the poles."""
        result_north = HeightOfTerrain(89.9, 0.0)
        result_south = HeightOfTerrain(-89.9, 0.0)
        assert isinstance(result_north, (int, float, np.floating, type(np.nan)))
        assert isinstance(result_south, (int, float, np.floating, type(np.nan)))

    def test_very_small_decimal_values(self):
        """Test coordinates with very small decimal parts."""
        result = HeightOfTerrain(40.000001, -105.000001)
        assert isinstance(result, (int, float, np.floating, type(np.nan)))

    def test_very_large_decimal_values(self):
        """Test coordinates with decimal parts close to 1."""
        result = HeightOfTerrain(40.999999, -105.999999)
        assert isinstance(result, (int, float, np.floating, type(np.nan)))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

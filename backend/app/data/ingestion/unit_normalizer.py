"""
Unit Normalization Layer for PS26080 (MoES / NCMRWF).
Provides centralized, deterministic unit conversions across GRIB2, NetCDF, and REST feeds.
Ensures scientific computation preserves standard SI / meteorological units.
"""

from typing import Optional, Tuple


class UnitNormalizer:
    """
    Centralized meteorological unit normalization.
    Standards:
    - Precipitation: mm (millimetres liquid equivalent)
    - Temperature: Kelvin (internal computation) / Celsius (display)
    - Pressure: hPa (hectopascals)
    - Wind: m/s (metres per second)
    - Relative Humidity: % [0.0 to 100.0]
    - Specific Humidity: g/kg (grams water vapor per kilogram moist air)
    """

    @staticmethod
    def precipitation_to_mm(value: Optional[float], from_unit: str = "kg m^-2") -> Optional[float]:
        """
        Convert precipitation to mm.
        1 kg m^-2 of liquid water at standard density = 1 mm depth.
        m/s (flux rate) * 3600 = mm/hour.
        m (accumulated meters) * 1000 = mm.
        """
        if value is None:
            return None
        
        unit = from_unit.strip().lower()
        if unit in ("kg m^-2", "kg/m^2", "kg m-2", "mm"):
            return round(float(value), 3)
        elif unit in ("m", "meters", "metre"):
            return round(float(value) * 1000.0, 3)
        elif unit in ("m s^-1", "m/s", "kg m^-2 s^-1"):
            # Flux rate to mm/hr
            return round(float(value) * 3600.0, 3)
        return round(float(value), 3)

    @staticmethod
    def temperature_to_kelvin(value: Optional[float], from_unit: str = "k") -> Optional[float]:
        """Normalize temperature to Kelvin."""
        if value is None:
            return None
        unit = from_unit.strip().lower()
        if unit in ("c", "celsius", "degc", "°c"):
            return round(float(value) + 273.15, 2)
        elif unit in ("f", "fahrenheit", "degf", "°f"):
            return round((float(value) - 32.0) * 5.0 / 9.0 + 273.15, 2)
        return round(float(value), 2)

    @staticmethod
    def temperature_to_celsius(value: Optional[float], from_unit: str = "k") -> Optional[float]:
        """Normalize temperature to Celsius."""
        if value is None:
            return None
        unit = from_unit.strip().lower()
        if unit in ("k", "kelvin"):
            return round(float(value) - 273.15, 2)
        elif unit in ("f", "fahrenheit", "degf", "°f"):
            return round((float(value) - 32.0) * 5.0 / 9.0, 2)
        return round(float(value), 2)

    @staticmethod
    def pressure_to_hpa(value: Optional[float], from_unit: str = "pa") -> Optional[float]:
        """
        Convert atmospheric pressure to hPa.
        100 Pa = 1 hPa = 1 mbar.
        """
        if value is None:
            return None
        unit = from_unit.strip().lower()
        if unit in ("pa", "pascals", "n/m^2"):
            return round(float(value) / 100.0, 2)
        elif unit in ("bar", "bars"):
            return round(float(value) * 1000.0, 2)
        elif unit in ("atm", "atmosphere"):
            return round(float(value) * 1013.25, 2)
        return round(float(value), 2)

    @staticmethod
    def wind_speed_to_ms(value: Optional[float], from_unit: str = "m/s") -> Optional[float]:
        """Convert wind speed to m/s."""
        if value is None:
            return None
        unit = from_unit.strip().lower()
        if unit in ("kt", "kts", "knots", "knot"):
            return round(float(value) * 0.514444, 2)
        elif unit in ("km/h", "kmh", "km/hr"):
            return round(float(value) / 3.6, 2)
        elif unit in ("mph", "miles/hour"):
            return round(float(value) * 0.44704, 2)
        return round(float(value), 2)

    @staticmethod
    def wind_speed_to_knots(value: Optional[float], from_unit: str = "m/s") -> Optional[float]:
        """Convert wind speed to knots (for aviation / meteorological presentation)."""
        if value is None:
            return None
        unit = from_unit.strip().lower()
        if unit in ("m/s", "ms", "m s^-1"):
            return round(float(value) * 1.94384, 2)
        elif unit in ("km/h", "kmh"):
            return round((float(value) / 3.6) * 1.94384, 2)
        return round(float(value), 2)

    @staticmethod
    def relative_humidity_to_percent(value: Optional[float], from_unit: str = "percent") -> Optional[float]:
        """Normalize relative humidity to [0.0, 100.0]%."""
        if value is None:
            return None
        unit = from_unit.strip().lower()
        val = float(value)
        # Check if expressed as fraction [0.0, 1.0]
        if unit in ("fraction", "ratio", "0-1") or (0.0 <= val <= 1.0 and unit != "percent"):
            val = val * 100.0
        return round(max(0.0, min(100.0, val)), 2)

    @staticmethod
    def specific_humidity_to_g_kg(value: Optional[float], from_unit: str = "kg/kg") -> Optional[float]:
        """Convert specific humidity to g/kg."""
        if value is None:
            return None
        unit = from_unit.strip().lower()
        if unit in ("kg/kg", "kg kg^-1", "fraction"):
            return round(float(value) * 1000.0, 3)
        return round(float(value), 3)

    @classmethod
    def normalize_temperature(cls, value: Optional[float], from_unit: str = "k") -> Optional[float]:
        """Normalize temperature (default target Celsius if from Kelvin, or to Kelvin)."""
        if from_unit.strip().lower() in ("k", "kelvin"):
            return cls.temperature_to_celsius(value, from_unit)
        return cls.temperature_to_kelvin(value, from_unit)

    @classmethod
    def normalize_pressure(cls, value: Optional[float], from_unit: str = "pa") -> Optional[float]:
        """Normalize pressure to hPa."""
        return cls.pressure_to_hpa(value, from_unit)

    @classmethod
    def normalize_precipitation(
        cls,
        value: Optional[float],
        from_unit: str = "kg m^-2",
        accumulation_hours: float = 1.0,
    ) -> Optional[float]:
        """Normalize precipitation rate/accumulation to mm."""
        return cls.precipitation_to_mm(value, from_unit)


# tests/test_logic.py
import pytest
import ipaddress
from pyside_ui.core.ip_ranges_txt import _find_ipv4, _net24_key, _range24

def test_find_ipv4():
    """Verifica que el extractor de IPs funcione con texto sucio."""
    text = "La IP es 192.168.1.5 y otra es 10.0.0.1, ignora esta: 999.999.999.999"
    ips = _find_ipv4(text)
    
    # _find_ipv4 devuelve objetos IPv4Address
    assert ipaddress.IPv4Address("192.168.1.5") in ips
    assert ipaddress.IPv4Address("10.0.0.1") in ips
    assert len(ips) == 2

def test_net24_key():
    """Verifica el cálculo del prefijo de red /24."""
    ip = ipaddress.IPv4Address("192.168.50.100")
    assert _net24_key(ip) == (192, 168, 50)

def test_range24():
    """Verifica el formato del rango IP final (estilo .1-.254)."""
    assert _range24(192, 168, 1) == "192.168.1.1-192.168.1.254"

"""
Schemdraw-based parametric circuit schematic generation for power supply designs.
Supports Buck, Boost, and LDO topologies with calculated component values.
"""

import schemdraw
import schemdraw.elements as elm


def generate_buck_schematic(Vin: float, Vout: float, Iout: float, fsw: float = 500e3) -> str:
    """Generate parametric Buck converter schematic."""
    # Calculate component values
    D = Vout / Vin
    delta_IL = 0.3 * Iout
    L = (Vin * D * (1 - D)) / (fsw * delta_IL)
    L_uH = L * 1e6

    delta_Vout = 0.01 * Vout
    Cout = delta_IL / (8 * fsw * delta_Vout)
    Cout_uF = Cout * 1e6

    d = schemdraw.Drawing()
    d.config(fontsize=10)

    # Input voltage source and capacitor
    d += elm.SourceSin().label(f'Vin={Vin}V', loc='top')
    d += elm.Line().right(0.3)
    d += elm.Capacitor().up().label('Cin', loc='top')
    d += elm.Ground()

    # Main path
    d += elm.Line().right(0.3)
    d += elm.NFet().right().label('Q1', loc='top')
    d += elm.Line().right(0.2)
    d += elm.Dot()

    # Inductor and output
    d.push()
    d += elm.Inductor().right().label(f'L={L_uH:.1f}uH', loc='top')
    d += elm.Dot()
    d += elm.Line().right(0.2)
    d += elm.Capacitor().down().label(f'Cout={Cout_uF:.1f}uF', loc='right')
    d.pop()

    # Load
    Rload = Vout / Iout
    d += elm.Line().down(0.2)
    d += elm.Resistor().down().label(f'{Rload:.1f}Ohm', loc='right')
    d += elm.Ground()

    # Freewheeling diode path (simplified)
    d.push()
    d += elm.Line().down(0.3)
    d += elm.Diode().right(0.5).label('D1', loc='bottom')
    d += elm.Line().up(0.3)
    d.pop()

    svg_bytes = d.get_imagedata('svg')
    return svg_bytes.decode('utf-8')


def generate_boost_schematic(Vin: float, Vout: float, Iout: float, fsw: float = 500e3) -> str:
    """Generate parametric Boost converter schematic."""
    D = 1 - (Vin / Vout)
    delta_IL = 0.3 * Iout * (Vout / Vin)
    L = (Vin * D) / (fsw * delta_IL)
    L_uH = L * 1e6

    delta_Vout = 0.01 * Vout
    Cout = Iout * D / (fsw * delta_Vout)
    Cout_uF = Cout * 1e6

    d = schemdraw.Drawing()
    d.config(fontsize=10)

    # Input
    d += elm.SourceSin().label(f'Vin={Vin}V', loc='top')
    d += elm.Line().right(0.3)
    d += elm.Capacitor().up().label('Cin', loc='top')
    d += elm.Ground()

    # Main path
    d += elm.Line().right(0.3)
    d += elm.Inductor().right().label(f'L={L_uH:.1f}uH', loc='top')
    d += elm.Dot()

    # Switch
    d.push()
    d += elm.Line().right(0.2)
    d += elm.NFet().right().label('Q1', loc='top')
    d += elm.Line().right(0.2)
    d.pop()

    # Output diode
    d += elm.Diode().up(0.5).label('D1', loc='right')
    d += elm.Line().right(0.3)
    d += elm.Dot()
    d += elm.Line().right(0.2)

    # Output filter and load
    d += elm.Capacitor().down().label(f'Cout={Cout_uF:.1f}uF', loc='right')

    Rload = Vout / Iout
    d.push()
    d += elm.Line().down(0.2)
    d += elm.Resistor().down().label(f'{Rload:.1f}Ohm', loc='right')
    d += elm.Ground()
    d.pop()

    svg_bytes = d.get_imagedata('svg')
    return svg_bytes.decode('utf-8')


def generate_ldo_schematic(Vin: float, Vout: float, Iout: float) -> str:
    """Generate parametric LDO regulator schematic."""
    d = schemdraw.Drawing()
    d.config(fontsize=10)

    # Input
    d += elm.SourceSin().label(f'Vin={Vin}V', loc='top')
    d += elm.Line().right(0.3)
    d += elm.Capacitor().up().label('Cin=1uF', loc='top')
    d += elm.Ground()

    # LDO regulator (using voltage source as simplified symbol)
    d += elm.Line().right(0.3)
    d += elm.SourceV().right().label('LDO', loc='top')
    d += elm.Line().right(0.3)

    # Output filter and load
    d += elm.Capacitor().down().label('Cout=10uF', loc='right')

    Rload = Vout / Iout
    d.push()
    d += elm.Line().down(0.2)
    d += elm.Resistor().down().label(f'{Rload:.1f}Ohm', loc='right')
    d += elm.Ground()
    d.pop()

    svg_bytes = d.get_imagedata('svg')
    return svg_bytes.decode('utf-8')


def generate_schematic(topology: str, Vin: float, Vout: float, Iout: float) -> str:
    """Generate circuit schematic for the specified topology.

    Args:
        topology: 'buck', 'boost', or 'ldo'
        Vin: Input voltage (V)
        Vout: Output voltage (V)
        Iout: Output current (A)

    Returns:
        SVG string of the schematic

    Raises:
        ValueError: If topology is not supported
    """
    topology = topology.lower().strip()

    if topology == 'buck':
        return generate_buck_schematic(Vin, Vout, Iout)
    elif topology == 'boost':
        return generate_boost_schematic(Vin, Vout, Iout)
    elif topology == 'ldo':
        return generate_ldo_schematic(Vin, Vout, Iout)
    else:
        raise ValueError(f"Unsupported topology: {topology}. Supported: 'buck', 'boost', 'ldo'")

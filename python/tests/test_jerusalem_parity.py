import pytest
from translated.ponto_blocks import (
    MTTraversalInput,
    BTTraversalInput,
    BTZeroTraversalInput,
    RamaisTraversalInput,
    calcular_polo,
)

def test_jerusalem_poste1_parity_v2():
    # MT1 T1 (C12-C18)
    # MT1 T2 (F12-F16)
    mt1 = [
        MTTraversalInput(           # T1 (C)
            tipo_rede="Convencional",
            tipo_cabo="397MCM-CA, Nu",
            vao=22.0,
            flecha=0.5,
            angulo=0.0,
            altura_poste=11.0,
            altura_ancoragem=9.2,
        ),
        MTTraversalInput(           # T2 (F)
            tipo_rede="Convencional",
            tipo_cabo="397MCM-CA, Nu",
            vao=18.0,
            flecha=0.5,
            angulo=172.0,
        ),
        MTTraversalInput(), # T3 inactive
        MTTraversalInput(), # T4 inactive
    ]
    
    # BT Inputs (C70=9.2, shared from MT1 T1)
    bt = [
        BTTraversalInput(altura_ancoragem=9.2),
        BTTraversalInput(),
        BTTraversalInput(),
        BTTraversalInput(),
    ]
    
    mt2 = [MTTraversalInput() for _ in range(4)]
    btz = [BTZeroTraversalInput() for _ in range(4)]
    ral = [RamaisTraversalInput() for _ in range(4)]
    
    # Perform calculation
    res = calcular_polo(mt1, mt2, bt, btz, ral)
    
    t1 = res.mt1.traversals[0]
    print(f"DEBUG MT1 T1: peso_total={t1.peso_total}, diam_total={t1.diam_total}")
    print(f"DEBUG MT1 T1: cat_H={t1.cat_H}, wind_H={t1.wind_H}")
    
    # GOLDEN values from Jerusalem Excel "Poste 1"
    TOL = 0.0001
    GOLDEN_RES = 73.12215577613182
    
    print(f"\nCalculated MT1 Resultante: {res.mt1.resultante}")
    print(f"Excel MT1 Resultante: {GOLDEN_RES}")
    
    assert res.mt1.resultante == pytest.approx(GOLDEN_RES, abs=TOL)
    # Check Tip Force (F33 in Excel)
    assert res.mt1.f_tip == pytest.approx(GOLDEN_RES, abs=TOL)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

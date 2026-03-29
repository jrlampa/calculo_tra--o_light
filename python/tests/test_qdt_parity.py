import pytest
from translated.qdt_blocks import QDTInput, calcular_qdt

def test_qdt_excel_parity():
    """
    Verify QDT calculation against the 'Alocação % de tensão' sheet values.
    Reference:
    L47=13200, O47=1.02, C48=75, F48=3.5, G48=4.5, H48=5.0, I48=1.5
    Excel results:
    S47=13464, V47=13110.57, V48=211.13, V49=203.22, I49=200.93
    """
    inp = QDTInput(
        v_nominal_mt=13200.0,
        v_nominal_bt=220.0,
        coef_perda=75.0,
        reg_mt=1.02,
        drop_mt_pct=3.5,
        drop_trafo_pct=4.5,
        drop_bt1_pct=5.0,
        drop_bt2_pct=1.5
    )

    res = calcular_qdt(inp)

    # Assertions with tolerance for rounding
    assert res.v_mt_initial == pytest.approx(13464.0, rel=0.001)
    assert res.v_mt_node == pytest.approx(13110.57, rel=0.001)
    assert res.v_bt_start == pytest.approx(211.13, rel=0.001)
    assert res.v_bt_node1 == pytest.approx(203.22, rel=0.001)
    assert res.v_bt_node2 == pytest.approx(200.93, rel=0.001)

    # Total drop check: 200.93 vs 220 -> (220-200.93)/220 = 8.66%
    assert res.drop_total_pct == pytest.approx(8.6675, rel=0.001)

if __name__ == "__main__":
    pytest.main([__file__])

# -*- coding: utf-8 -*-
def CRF(WACC, Lifetime):
    """
    Calculate Capital Recovery Factor
    
    Parameters:
    WACC: Weighted Average Cost of Capital (decimal)
    Lifetime: Asset lifetime in years
    
    Returns:
    Capital Recovery Factor
    """
    return (WACC * (1 + WACC)**Lifetime) / ((1 + WACC)**Lifetime - 1)

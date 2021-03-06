

def ME_CW_Pump(rpm,pressure):
    "Engine driven cooling water pump HT/LT for ME. Inputs engine-rpm and gauge-pressure [bar] CW."
    # The equation was derived from the pump diagram in the engine project manual at 500 rpm
    # H = -0.0004 Q^2 + 0.0317 Q + 28.47
    # pq-formula: ax^2 + bx + c = 0
    # Affinity laws
    #if pressure < 1:
    #    print('Out of domain, P')
    # The pump formula is for 500 rpm. So the pressure input must be scaled so
    # it "fits" the right rpm using the affinity laws
    static_head = 10
    H = ((pressure * 1.e5) / (9.81 * 1000) - static_head) * (500./rpm)**2

    a = -0.0004
    b = 0.0317
    c = 28.48 - H
    # pq-formula, only the positive
    Q = -b/(2*a) + sqrt( (b**2) / ((2*a)**2) - (c / a) )

    # The value which is calculated is for if the pump was running on 500 rpm
    # Account for the affinity laws
    Q_out = Q * (rpm/500.)
    return Q_out

def AE_CW_Pump(rpm,pressure):
    "Engine driven cooling water pump HT/LT for AE. Inputs engine-rpm and gauge-pressure [bar] CW."
    # The equation was derived from the pump diagram in the engine project manual at 750 rpm
    # H = -0.0017 Q^2 - 0.0136 Q + 34.783
    # pq-formula: ax^2 + bx + c = 0
    # Affinity laws
    # The pump formula is for 750 rpm. So the pressure input must be scaled so
    # it "fits" the right rpm using the affinity laws
    static_head = 10
    H = ((pressure * 1.e5) / (9.81 * 1000) - static_head) * (750./rpm)**2

    a = -0.0017
    b = -0.0136
    c = 34.783 - H
    # pq-formula, only the positive
    Q = -b/(2*a) + sqrt( (b**2) / ((2*a)**2) - (c / a) )

    # The value which is calculated is for if the pump was running on 500 rpm
    # Account for the affinity laws
    Q_out = Q * (rpm/500.)
    return Q_out

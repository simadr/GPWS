import math

def ftmin_to_ms(vz):
    return 0.00508*vz

def ft_to_m(z):
    return 0.3048*z

def create_testMode1(vzi, vzf, ralti, raltf, nb_points, filename):
    x=0
    y=0
    z=0
    fpa = -3*math.pi/180
    psi=0
    phi=0
    pas_vz = (vzf - vzi) / nb_points
    pas_ralt = (ralti - raltf) / nb_points
    vz = vzi
    ralt = ralti
    fic = open(filename, "w")
    for i in range(nb_points):
        time = "Time t={}\n".format(i)
        radio_alt =  "RadioAltimeter groundAlt={}\n".format(ralt)
        vp = vz/math.sin(fpa)
        statevector = "StateVector x={0} y={1} z={2} Vp={3} fpa={4} psi={5} phi={6}\n".format(x, y, z, vp, fpa, psi, phi)
        fic.write(time)
        fic.write(radio_alt)
        fic.write(statevector)
        vz += pas_vz
        ralt += pas_ralt
    fic.close()


create_testMode1(ftmin_to_ms(-1500), ftmin_to_ms(-6225), ft_to_m(2500), ft_to_m(370), 10, "test_mode1.txt")
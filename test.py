import math, matplotlib.pyplot as plt, matplotlib, numpy as np
from matplotlib.patches import Polygon, Circle
from matplotlib.collections import PatchCollection
import gpws

def ftmin_to_ms(vz):
    return 0.00508*vz

def ft_to_m(z):
    return 0.3048*z

def plot_mode(mode, fig=None, ax=None):
    """
    :param mode: Classe d'un mode
    :return: Dessine les enveloppes d'un mode
    """
    if fig == None or ax==None:
        fig, ax = plt.subplots()
    patches = []
    for env in mode.list_enveloppes:
        polygon = Polygon(env.vertexes, True)
        patches.append(polygon)
    p = PatchCollection(patches,  alpha=0.2)

    colors = [i for i in range(len(mode.list_enveloppes))]
    p.set_array(np.array(colors))

    ax.add_collection(p)
    plt.autoscale()
    if fig == None or ax==None:
        plt.show()

def plot_trajectory(traj, mode, flaps, gear):
    """
    :param traj: Liste de points
    :param mode: Mode
    :return: Plot les points de la trajectoire de la forme associee a l'enveloppe dans laquelle ils se trouvent
    """
    fig, ax = plt.subplots()
    plot_mode(mode, fig ,ax)
    markers = ['o', 'v', '^', '<', '>', '8', 's', 'p']
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']


    for (x,y) in traj:
        env = mode.get_enveloppe((x,y), flaps, gear)
        if env == None:
            marker = markers[0]
            color =  colors[0]
        else:
            i = mode.list_enveloppes.index(env)
            marker = markers[i + 1]
            color= colors[i + 1]
        plt.plot(x, y, marker, color=color)

    nb_env = len(mode.list_enveloppes)
    legends = [plt.Line2D((0,1),(0,0), marker=markers[0], linestyle='', color= colors[0])]
    description = ['Hors enveloppe']
    for i in range(nb_env):
        legends.append(plt.Line2D((0,1),(0,0), marker=markers[i+1], linestyle='', color= colors[i+1]))
        description.append(mode.list_enveloppes[i].name)
    ax.legend(legends, description)
    plt.autoscale()
    plt.show()

def create_testMode1(vzi, vzf, ralti, raltf, nb_points, filename):
    x=0
    y=0
    z=0
    fpa = -3*math.pi/180
    psi=0
    phi=0
    pas_vz = (vzf - vzi) / nb_points
    pas_ralt = (raltf - ralti) / nb_points
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

def create_test(mode, gamma, absi, absf, ordi, ordf, nb_points, filename):
    """ Creer un fichier de test a partir d'un mode, d'un gamma (constant ici), d'un point initial et final  """
    etat = gpws.Etat(0,0,0,0,0,0,0)
    pas_abs = (absf - absi) / nb_points
    pas_ord = (ordf - ordi) / nb_points
    abs = absi
    ord = ordi
    fic = open(filename, "w")
    for i in range(nb_points):
        etat.set_xy(abs, ord, mode)
        time = "Time t={}\n".format(i)
        radio_alt =  etat.generate_radioalt()
        statevector = etat.generate_statevector(gamma)
        fic.write(time)
        fic.write(radio_alt)
        fic.write(statevector)
        abs += pas_abs
        ord += pas_ord
    fic.close()

# traj = [[1500, 2500],[ 6225, 370], [3800, 1450]]
# mode = gpws.Mode1
# plot_trajectory(traj,mode, 1, 1)

create_testMode1(ftmin_to_ms(-1500), ftmin_to_ms(-6225), ft_to_m(2500), ft_to_m(370), 10, "toto.txt")
create_test(gpws.Mode1, -3*math.pi/180, -1500, -6225, 2500, 370, 10, "test_mode1.txt")
create_test(gpws.Mode4, -10*math.pi/180, 100, 300, 1000, 245, 10, "test_mode4.txt")
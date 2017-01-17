from ivy.std_api import *
import sys, logging, math
logger = logging.getLogger('Ivy')
from optparse import OptionParser


try:
    import pygame
    TEST_SON = True
except ImportError:
    print("Module pygame non installe : impossible de lire les sons")
    TEST_SON = False

# Abcsisses/Ordornnees des modes
VZ = 0
RADIOALT = 1
TERRAIN_CLOSURE_RATE = 2
MSL_ALT_LOSS = 3
COMPUTED_AIR_SPEED = 4
GLIDE_SLOPE_DEVIATION = 5
ROLL_ANGLE = 6


#Coefficents de conversion
FTMIN_TO_MS = 0.00508
KTS_TO_MS = 0.514444
FT_TO_M = 0.3048
MS_TO_KTS = 1.94384

#Gear
DOWN = "Down"
UP = "Up"

#Phase
APP = "APPROACH"
CLIMB = "CLIMB"
TAKEOFF  = "TAKE-OFF"
LDG = "LANDING"

#Callouts
CALLOUTS = [(0, "sons/nappminimuns.wav)"), (10,"sons/abn10.wav"), (20,"sons/abn20.wav"), (30,"sons/abn30.wav"),
            (40,"sons/abn40.wav"),
            (50,"sons/abn50.wav"), (100, "sons/abn100.wav"), (500, "sons/abn500"),
            (1000, "sons/abn1000.wav"), (2500, "sons/abn2500.wav")]

#Ivy messages
PULLUP_MSG = "Pullup={}"
STOP_PULLUP_UP_MSG = "StopPullup"


def play_sound(sound):
    """
    Joue un son
    :param sound: chemin du sons a jouer
    :return: ()
    """
    if TEST_SON:
        pygame.init()
        song = pygame.mixer.Sound(sound)
        song.play()
        while pygame.mixer.get_busy():
             pygame.time.delay(100)
        pygame.quit()
    else:
        print("Lecture de ", sound)

#Classes
class Enveloppe():
    def __init__(self, vertexes, alertlevel, priority, flaps, gear, name, sound, pullup=False):
        self.vertexes = vertexes
        self.alertlevel = alertlevel
        self.priority = priority
        self.flaps = flaps
        self.gear = gear
        self.sound = sound
        self.name = name
        self.pullup = pullup

    def collision(self,P):
        """
        :param P: point de coordonees (x,y)
        :return: True si le point est dans le polygone definissant l'enveloppe
        """
        graphe = self.vertexes
        nbp = len(graphe)
        for i in range(0,nbp):
            A = graphe[i]
            if i == nbp-1:
                B = graphe[0]
            else:
                B = graphe[i+1]
            AB = [0,0]
            AP = [0,0]
            AB[0] = B[0] - A[0]
            AB[1] = B[1] - A[1]
            AP[0] = P[0] - A[0]
            AP[1] = P[1] - A[1]
            d = AB[0]*AP[1] - AB[1]*AP[0]
            if d>0 :
                return False
        return True

    def have_inside(self, point, flaps, gear):
        """

        :param point: Point de coord x,y
        :param flaps: position des flaps
        :param gear: position des gears
        :return: True si dans la config consideree, le point est dans l'enveloppe
        """
        if (flaps not in self.flaps and self.flaps[0] != None) or (gear not in self.gear and self.gear[0] != None): # Si la config n'est pas bonne
            return False
        else:
            return self.collision(point)

    def play_sound(self):
        """Joue l'alarme de l'env"""
        play_sound(self.sound)

    def __repr__(self):
        return self.name

class Mode():
    def __init__(self, list_enveloppes, phase, abs, ord, name):
        self.list_enveloppes = list_enveloppes
        self.phase = phase
        self.on = True
        self.ord = ord
        self.abs = abs
        self.name = name

    def get_enveloppe(self, point, flaps, gear):
        """

        :param point: point x,y
        :param flaps: position des flaps
        :param gear: position du gear
        :return: L'enveloppe dans lequel se trouve le point dans la configuration consideree, None sion
        """
        enveloppe_eff = [] #listes des enveloppes ou se trouve le point
        for env in self.list_enveloppes:
            if env.have_inside(point, flaps, gear):
                enveloppe_eff.append(env)
        if len(enveloppe_eff) == 0:
            return None #Le point n'est dans aucune enveloppe
        else:
            key_sort = lambda env : env.priority
            enveloppe_eff.sort(key=key_sort) #On trie selon la plus petite prioritee
            return enveloppe_eff[0]


    def get_xmin_ymin_xmax_ymax(self):
        """ Retourne les coordonnees extremes des enveloppes du mode (utile pour les tests)"""

        xmin = xmax = self.list_enveloppes[0].vertexes[0][0]
        ymin = ymax = self.list_enveloppes[0].vertexes[0][1]
        for env in self.list_enveloppes:
            for (x, y) in env.vertexes:
                if x < xmin:
                   xmin = x
                elif x > xmax:
                    xmax = x
                if y < ymin:
                    ymin = y
                elif y > ymax:
                    ymax = y
        return (xmin, ymin, xmax, ymax)


    def disable(self):
        self.on = False

    def enable(self):
        self.on = True

class Etat():
    def __init__(self,VerticalSpeed,RadioAltitude,TerrainClosureRate,MSLAltitudeLoss,ComputedAirSpeed,GlideSlopeDeviation,RollAngle,flaps,gear,phase):
        self.list = [VerticalSpeed, RadioAltitude, TerrainClosureRate, MSLAltitudeLoss, ComputedAirSpeed, GlideSlopeDeviation, RollAngle]
        self.flaps = flaps
        self.gear = gear
        self.phase = phase
        self.da = 0
        self.dh = 0
        self.time = 0

        self.last_radio = 0 #dernier temps ou on a recu l'info de radio alt

        self.is_pullup = False #Savoir si on est en situation de pullup

        self.last_callout = len(CALLOUTS) #Definie le dernier callout effectue

        self.max_ralt = 0 # POur connaitre le msl altitude loss

        # Attribut permettant de savoir si l'etat est correctement initialise
        self.init_ralt = False
        self.init_state = False
        self.init_fms = False
        self.init_config = False


    def get_VerticalSpeed(self):
        return self.list[VZ]

    def get_RadioAltitude(self):
        return self.list[RADIOALT]

    def get_TerrainClosureRate(self):
        return self.list[TERRAIN_CLOSURE_RATE]

    def get_MSLAltitudeLoss(self):
        return self.list[MSL_ALT_LOSS]

    def get_ComputedAirSpeed(self):
        return self.list[COMPUTED_AIR_SPEED]

    def get_GlideSlopeDeviation(self):
        return self.list[GLIDE_SLOPE_DEVIATION]

    def get_RollAngle(self):
        return self.list[ROLL_ANGLE]

    def generate_radioalt(self):
        """ Pour les tests uniquement """
        return "RadioAltimeter groundAlt={}\n".format(self.list[RADIOALT] * FT_TO_M)

    def generate_statevector(self, gamma):
        """ Pour les tests uniquement """
        x = 0
        y = 0
        z = 0
        fpa = gamma
        if gamma !=0 and self.get_VerticalSpeed() != 0 and self.get_ComputedAirSpeed() == None:
            vp = abs(self.get_VerticalSpeed()/math.sin(gamma)) * FTMIN_TO_MS #Conversion ft/min to m/s
        else: vp = self.get_ComputedAirSpeed() / MS_TO_KTS# Conversion kts to m/s
        psi = 0
        phi = math.radians(self.get_RollAngle())
        return "StateVector x={0} y={1} z={2} Vp={3} fpa={4} psi={5} phi={6}\n".format(x, y, z, vp, fpa, psi, phi)

    def generate_fms(self):
        """ Pour les tests uniquement """
        return "FMS_TO_GPWS phase={0}, da={1}, dh={2}\n".format(self.phase, self.da, self.dh)

    def generate_config(self):
        """ Pour les tests uniquement """
        return "Config GEAR={} FLAPS={}\n".format(self.gear, self.flaps)

    def get_xy(self, mode):
        x = self.list[mode.abs]
        y = self.list[mode.ord]
        return (x, y)

    def set_xy(self, x, y, mode, gamma=0):
        """  Modifie l'etat de sorte qu'il se trouve aux coord (x,y) dans le mode passe en param (pour test uniquement) """
        self.list[mode.abs] = x
        self.list[mode.ord] = y
        if mode.abs == VZ and gamma != 0:  #si on change la vz, on change la vp
            self.list[COMPUTED_AIR_SPEED]  =   (x * FTMIN_TO_MS)/( math.sin(abs(gamma)) * KTS_TO_MS)
        elif mode.abs == COMPUTED_AIR_SPEED:
            self.list[VZ] =  - self.get_ComputedAirSpeed() * math.sin(gamma) * KTS_TO_MS / FTMIN_TO_MS
        if self.get_ComputedAirSpeed() == None:
            self.list[COMPUTED_AIR_SPEED] = 0



    def change_radio_alt(self, z):
        z = z / FT_TO_M #conversion m to ft
        if global_etat.init_ralt and  (self.time - self.last_radio) != 0: #On met a jour le terrain closure rate si possible
            self.list[TERRAIN_CLOSURE_RATE] = ((self.get_RadioAltitude() - z)/ (self.time - self.last_radio) )  * 60
        self.list[RADIOALT] = z
        self.last_radio = self.time

    def change_state(self, x, y, z, vp, fpa, psi, phi):
        self.list[COMPUTED_AIR_SPEED] = vp * MS_TO_KTS #conversion ms to kts
        self.list[VZ] =  - (math.sin(fpa) * vp) / FTMIN_TO_MS #conversion m/s to - ft/min
        self.list[ROLL_ANGLE] = math.degrees(abs(phi))

    def change_fmsinfo(self, phase, da, dh):
        self.phase = phase
        self.da = da
        self.dh = dh
        alt_diff = self.max_ralt - self.get_RadioAltitude()
        if self.phase == TAKEOFF and self.init_ralt and (self.max_ralt - self.get_RadioAltitude() < 0) and self.get_VerticalSpeed() > 0:
            self.list[MSL_ALT_LOSS] = alt_diff
        else:
            self.list[MSL_ALT_LOSS] = 0


    def change_config(self, flaps, gear):
        self.flaps = flaps
        self.gear = gear

    def callout(self):
        if self.phase == APP and self.get_VerticalSpeed() > 0 :
            ralt = self.get_RadioAltitude()
            for i in range(self.last_callout):
                (callout, sound) = CALLOUTS[i]
                if ralt <= callout + self.dh:
                    play_sound(sound)
                    print("Callout:  {}".format(callout))
                    self.last_callout = i
                    break



    def is_init(self):
        return self.init_config and self.init_fms and self.init_ralt and self.init_state

    def __copy__(self):
        copy = Etat(self.get_VerticalSpeed(), self.get_RadioAltitude(), self.get_TerrainClosureRate(),
                    self.get_MSLAltitudeLoss(), self.get_ComputedAirSpeed(), self.get_GlideSlopeDeviation(),
                    self.get_RollAngle(), self.flaps, self.gear, self.phase
                    )
        copy.da = self.da
        copy.dh = self.dh
        copy.init_fms = self.init_fms
        copy.init_ralt = self.init_ralt
        copy.init_state = self.init_state
        copy.init_config = self.init_config
        return copy


    def __repr__(self):
        to_print = ""
        to_print +=  "Vertical speed = {}\n".format(self.get_VerticalSpeed())
        to_print +=  "Radio_alt = {}\n".format(self.get_RadioAltitude())
        to_print +=  "Terrain closure rate = {}\n".format(self.get_TerrainClosureRate())
        to_print +=  "MSl altitude loss = {}\n".format(self.get_MSLAltitudeLoss())
        to_print +=  "Computed airspeed = {}\n".format(self.get_ComputedAirSpeed())
        to_print +=  "GlideslopeDeviation = {}\n".format(self.get_GlideSlopeDeviation())
        to_print +=  "Roll angle = {}\n".format(self.get_RollAngle())
        return to_print

def Creation_Modes():

    PullUp1 = Enveloppe([[1750,370],[3000,1000],[6225,2075],[8000,2075],[8000,0],[1750,0]],'W',2,[None],[None],
                        "Pullup_rate_sink", "sons/nabpullup.wav", pullup=True)
    SinkRate1 = Enveloppe([[1750,370],[2610,1180],[5150,2450],[8000,2450],[8000,0],[1750,0]],'C',17,[None],[None],
                          "Sink rate", "sons/nabsinkrate.wav")
    PullUp2 = Enveloppe([[2277,220],[3000,790],[8000,790],[8000,0],[2277,0]],'W',3,[None],[None], "Pullup_terrain",
                        "sons/nabterrainaheadpullup.wav", pullup=True)
    Terrain2 = Enveloppe([[2277,220],[3000,790],[3900,1500],[6000,1800],[8000,1800],[8000,0],[2277,0]],'C',9,["0"],
                         [None], "Terrain", "sons/nabterrain.wav")
    DontSink3 = Enveloppe([[0,0],[143,1500],[400,1500],[400,0]],'C',18,[None],[None], "Don't sink",
                          "sons/ndontsink.wav")
    TooLowTerrain4 = Enveloppe([[190,0],[190,500],[250,1000],[400,1000],[400,0],[190,0]],'W',4,[None],[None],
                               "Too low terrain", "sons/TooLowTerrain.wav")
    TooLowFlaps4 = Enveloppe([[0,0],[0,245],[190,245],[190,0]],'C',16,["0"],[None], "Too low flaps",
                             "sons/nabtoolowflaps.wav")
    TooLowGear4 = Enveloppe([[0,0],[0,500],[190,500],[190,0]],'C',15,[None],[UP], "Too low gear",
                            "sons/nabtoolowgear.wav")
    GlideSlope5 = Enveloppe([[2,300],[4,300],[4,0],[3.68,0],[2,150]],'C',19,[None],[DOWN],
                            "GLIDESLOPE", "sons/nabglideslope2.wav")
    GlideSlopeReduced5 = Enveloppe([[1.3,1000],[4,1000],[4,0],[2.98,0],[1.3,150]],'C',19.5,[None],[DOWN],
                                   "Glideslope (reduced)", "sons/nabglideslope.wav")
    ExRollAngle_16 = Enveloppe([[10,30],[40,150],[40,0],[10,0]],'C',22,[None],[None], "Bank angle",
                               "sons/nbankangle.wav")
    ExRollAngle_26 = Enveloppe([[40,0],[40,5000],[180,5000],[180,0]],'C',22,[None],[None], "Bank angle",
                               "sons/nbankangle.wav")


    Mode1 = Mode([PullUp1,SinkRate1],[None],VZ,RADIOALT, "mode1")
    Mode2 = Mode([PullUp2,Terrain2], [None],TERRAIN_CLOSURE_RATE,RADIOALT, "mode2")
    Mode3 = Mode([DontSink3],[CLIMB],MSL_ALT_LOSS,RADIOALT, "mode3")
    Mode4 = Mode([TooLowTerrain4,TooLowFlaps4,TooLowGear4], [APP, LDG, TAKEOFF], COMPUTED_AIR_SPEED, RADIOALT, "mode4")
    Mode5 = Mode([GlideSlopeReduced5,GlideSlope5],[APP],GLIDE_SLOPE_DEVIATION,RADIOALT, "mode5")
    Mode5.disable()
    Mode6 = Mode([ExRollAngle_16, ExRollAngle_26],[None],ROLL_ANGLE,RADIOALT, "mode6")

    return [Mode1,Mode2,Mode3,Mode4,Mode5,Mode6]

L_Modes = Creation_Modes()

def test_mode(Etat):
    active_mode = [mode for mode in L_Modes if mode.on]
    flaps = Etat.flaps
    gear = Etat.gear
    L = []
    for Mode in active_mode:
        if Etat.phase in Mode.phase or Mode.phase[0] == None:
            x,y = Etat.get_xy(Mode)
            L.append(Mode.get_enveloppe([x,y],flaps,gear))
    L = [e for e in L if e!= None]
    key_sort = lambda env : env.priority
    L.sort(key=key_sort) #On trie selon la plus petite prioritee
    return (L[0] if len(L)!=0 else None)

def alert(env, etat):
    print ("alert : {}".format(env.name))
    env.play_sound()
    if env.pullup:
        IvySendMsg(PULLUP_MSG.format(env.name))
        etat.is_pullup = True
    else:
        if etat.is_pullup:
            print("Stop pull up")
            IvySendMsg(STOP_PULLUP_UP_MSG)
        etat.is_pullup = False


## Variables globals
global_etat = Etat(0,0,0, 0, 0, 0, 0, 0,"Down","LANDING")


if __name__ == '__main__':
    #parse
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.set_defaults(ivy_bus="127.255.255.255:2010", interval=5, verbose=False, app_name="GPWS")
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                      help='Be verbose.')
    parser.add_option('-i', '--interval', type='int', dest='interval',
                      help='Interval between messages (in seconds)')
    parser.add_option('-b', '--ivybus', type='string', dest='ivy_bus',
                      help='Bus id (format @IP:port, default to 127.255.255.255:2010)')
    parser.add_option('-a', '--appname', type='string', dest='app_name',
                      help='Application Name')
    (options, args) = parser.parse_args()

    # init log
    level = logging.INFO
    if options.verbose: # update logging level
        level = logging.DEBUG
    logger.setLevel(level)

    #### IVY ####
    def on_cx_proc(agent, connected):
        if connected == IvyApplicationDisconnected:
            logger.error('Ivy application %r was disconnected', agent)
        else:
            logger.info('Ivy application %r was connected', agent)


    def on_die_proc(agent, _id):
        logger.info('received the order to die from %r with id = %d', agent, _id)


    def connect(app_name, ivy_bus):
        IvyInit(app_name,                   # application name for Ivy
                "[%s ready]" % app_name,    # ready message
                0,                          # main loop is local (ie. using IvyMainloop)
                on_cx_proc,                 # handler called on connection/disconnection
                on_die_proc)
        IvyStart(ivy_bus)

    def on_time(agent, *larg):
        t = float(larg[0])
        global_etat.time = t
        if global_etat.init_ralt and global_etat.init_fms:
            global_etat.callout()
        if global_etat.is_init():
            env = test_mode(global_etat)
            if env != None:
                alert(env, global_etat)
        else:
            print("GPWS NOT INITIALIZED")
        print global_etat


    def on_radioalt(agent, *larg):
        z = float(larg[0])
        logger.info("Receive radio altitude : %s" % z)
        global_etat.change_radio_alt(z)
        global_etat.init_ralt = True

    def on_statevector(agent, *larg):
        x = float(larg[0])
        y = float(larg[1])
        z = float(larg[2])
        vp = float(larg[3])
        fpa = float(larg[4])
        psi = float(larg[5])
        phi = float(larg[6])
        global_etat.change_state(x, y, z, vp, fpa, psi, phi)
        global_etat.init_state = True

    def on_fms(agent, *larg):
        phase = larg[0]
        da = float(larg[1])
        dh = float(larg[2])
        global_etat.change_fmsinfo(phase, da, dh)
        global_etat.init_fms = True

    def on_config(agent, *larg):
        gear = larg[0]
        flaps = larg[1]
        global_etat.change_config(flaps, gear)
        global_etat.init_config = True


    connect(options.app_name, options.ivy_bus)
    IvyBindMsg(on_time, '^Time t=(\S+)')
    IvyBindMsg(on_radioalt, '^RadioAltimeter groundAlt=(\S+)')
    IvyBindMsg(on_statevector, 'StateVector\s+x=(\S+)\s+y=(\S+)\sz=(\S+)\sVp=(\S+)\sfpa=(\S+)\spsi=(\S+)\sphi=(\S+)')
    IvyBindMsg(on_fms, '^FMS_TO_GPWS\sphase=(\S+),\sda=(\S+),\sdh=(\S+)')
    IvyBindMsg(on_config, 'Config\s+GEAR=(\S+)\s+FLAPS=(\S+)')
    IvyMainLoop()

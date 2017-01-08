try:
    import pygame
    TEST_SON = True
except ImportError:
    print("Module pygame non installe : impossible de lire les sons")
    TEST_SON = False

class Enveloppe():
    def __init__(self, vertexes, alertlevel, priority, flaps, gear, phase):
        self.vertexes = vertexes
        self.alertlevel = alertlevel
        self.priority = priority
        self.flaps = flaps
        self.gear = gear
        self.phase = phase
        self.sound = "sons/abn2500.wav" # to change

    def collision(self,P):
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
        if (flaps != self.flaps and self.flaps != None) or (gear != self.gear and self.gear != None): # Si la config n'est pas bonne
            return False
        else:
            return self.collision(point)

    def play_sound(self):
        if TEST_SON:
            pygame.init()
            song = pygame.mixer.Sound(self.sound)
            song.play()
            while pygame.mixer.get_busy():
                 pygame.time.delay(100)
            pygame.quit()
        else:
            print("Lecture de ", self.sound)

class Mode():
    def __init__(self, list_enveloppes,phase):
        self.list_enveloppes = list_enveloppes
        self.phase = phase
        self.on = True

    def get_enveloppe(self, point, flaps, gear):
        enveloppe_eff = [] #listes des enveloppes ou se trouve le point
        for env in self.list_enveloppes:
            if env.have_inside(point, flaps, gear):
                enveloppe_eff.append(env)
        if len(enveloppe_eff) == 0:
            return None #Le point n'est dans aucune enveloppe
        else:
            key_sort = lambda env : env.priority
            enveloppe_eff.sort(key=key_sort, reverse=True) #On trie selon la plus grande prioritee
            return enveloppe_eff

class Etat():
    def __init__(self,VerticalSpeed,RadioAltitude,TerrainClosureRate,MSLAltitudeLoss,ComputedAirSpeed,GlideSlopeDeviation,RollAngle,HeightAboveTerrain):
        self.VerticalSpeed = VerticalSpeed
        self.RadioAltitude = RadioAltitude
        self.TerrainClosureRate = TerrainClosureRate
        self.MSLAltitudeLoss = MSLAltitudeLoss
        self.ComputedAirSpeed = ComputedAirSpeed
        self.GlideSlopeDeviation = GlideSlopeDeviation
        self.RollAngle = RollAngle
        self.HeightAboveTerrain = HeightAboveTerrain


PullUp1 = Enveloppe([[1750,370],[3000,1000],[6225,2075],[8000,2075],[8000,0],[1750,0]],0,1,None,None,1)
SinkRate1 = Enveloppe([[1750,370],[2610,1180],[5150,2450],[8000,2450],[8000,0],[1750,0]],1,1,None,None,1)

PullUp2 = Enveloppe([[2277,220],[3000,790],[8000,790],[8000,0],[2277,0]],0,1,None,1,1)
Terrain2 = Enveloppe([[2277,220],[3000,790],[3900,1500],[6000,1800],[8000,1800],[8000,0],[2277,0]],1,1,None,None,1)

DontSink3 = Enveloppe([[0,0],[143,1500],[400,1500],[400,0]],1,1,None,None,1)

TooLowTerrain4 = Enveloppe([[190,0],[190,500],[250,1000],[400,1000],[400,0],[190,0]],1,1,None,None,1)
TooLowFlaps4 = Enveloppe([[0,0],[0,245],[190,245],[190,0]],1,1,None,None,1)
TooLowGear4 = Enveloppe([[0,0],[0,500],[190,500],[190,0]],1,1,None,None,1)

GlideSlopeReduced5 = Enveloppe([[1.3,1000],[4,1000],[4,0],[2.98,0],[1.3,150]],1,1,None,None,1)
GlideSlope5 = Enveloppe([[2,300],[4,300],[4,0],[3.68,0],[2,150]],1,1,1,1,1)

ExRollAngle6 = Enveloppe([[10,30],[40,150],[40,500],[90,500],[-90,500],[-40,500],[-40,150],[-10,30]],1,1,None,None,1)

Etat0 = Etat(0, 0, 0, 0, 0, 0, 0, 0)

def test_mode(Etat):
    #Mode 1
    Mode1 = Mode([PullUp1,SinkRate1],None)
    x1 = Etat.VerticalSpeed # ft/mn
    y1 = Etat.RadioAltitude # ft
    #print(PullUp1.collision([x1,y1]))
    #print(SinkRate1.collision([x1,y1]))
    print(Mode1.get_enveloppe([x1,y1],None,None))

    #Mode 2
    Mode2 = Mode([PullUp2,Terrain2],None)
    x2 = Etat.TerrainClosureRate # ft/mn
    y2 = Etat.RadioAltitude # ft
    # print(PullUp2.collision([x2,y2]))
    # print(Terrain2.collision([x2,y2]))
    print(Mode2.get_enveloppe([x2,y2],None,None))

    #Mode 3
    Mode3 = Mode([DontSink3],"Takeoff")
    x3 = Etat.MSLAltitudeLoss # ft
    y3 = Etat.RadioAltitude # ft
    print(DontSink3.collision([x3,y3]))
    print(Mode3.get_enveloppe([x3,y3],None,None))

    #Mode 4
    Mode4 = Mode([TooLowTerrain4,TooLowFlaps4,TooLowGear4],None)
    x4 = Etat.ComputedAirSpeed # kts
    y4 = Etat.RadioAltitude # ft
    # print(TooLowTerrain4.collision([x4,y4]))
    # print(TooLowFlaps4.collision([x4,y4]))
    # print(TooLowGear4.collision([x4,y4]))
    print(Mode4.get_enveloppe([x4,y4],None,None))

    #Mode 5
    x5 = Etat.GlideSlopeDeviation# dots
    y5 = Etat.RadioAltitude # ft
    Mode5 = Mode([GlideSlopeReduced5,GlideSlope5],"Approach")
    # print(GlideSlopeReduced5.collision([x5,y5]))
    # print(GlideSlope5.collision([x5,y5]))
    print(Mode5.get_enveloppe([x5,y5],None,None))

    #Mode 6

    Mode6 = Mode([ExRollAngle6],0)
    x6 = Etat.RollAngle # degrees
    y6 = Etat.HeightAboveTerrain # ft
    # print(ExRollAngle6.collision([x6,y6]))
    print(Mode6.get_enveloppe([x6,y6],None,None))
    ExRollAngle6.play_sound()

test_mode(Etat0)
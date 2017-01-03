UP = "0"
DOWN = "1"

class Enveloppe():
    def __init__(self, vertexes, alertlevel, priority, flaps, gears, phase):
        self.vertexes = vertexes
        self.alertlevel = alertlevel
        self.priority =priority
        self.flaps = flaps
        self.gears = gears
        self.phase = phase
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

class Mode():
    def __init__(self, list_enveloppes):
        self.list_enveloppes = list_enveloppes

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


Entree = Etat(0,0,0,0,0,0,0,0)

#Mode 1
x1 = Entree.VerticalSpeed # ft/mn
y1 = Entree.RadioAltitude # ft

PullUp1 = Enveloppe([[1750,370],[3000,1000],[6225,2075],[8000,2075],[8000,0],[1750,0]],1,1,1,1,1)
SinkRate1 = Enveloppe([[1750,370],[2610,1180],[5150,2450],[8000,2450],[8000,0],[1750,0]],1,1,1,1,1)

print(PullUp1.collision([x1,y1]))
print(SinkRate1.collision([x1,y1]))

#Mode 2

x2 = Entree.TerrainClosureRate # ft/mn
y2 = Entree.RadioAltitude # ft

PullUp2 = Enveloppe([[2277,220],[3000,790],[8000,790],[8000,0],[2277,0]],1,1,1,1,1)
Terrain2 = Enveloppe([[2277,220],[3000,790],[3900,1500],[6000,1800],[8000,1800],[8000,0],[2277,0]],1,1,1,1,1)

print(PullUp2.collision([x2,y2]))
print(Terrain2.collision([x2,y2]))

#Mode 3

x3 = Entree.MSLAltitudeLoss # ft
y3 = Entree.RadioAltitude # ft

DontSink = Enveloppe([[0,0],[143,1500],[400,1500],[400,0]],1,1,1,1,1)

print(DontSink.collision([x3,y3]))

#Mode 4

x4 = Entree.ComputedAirSpeed # kts
y4 = Entree.RadioAltitude # ft


TooLowTerrain4 = Enveloppe([[190,0],[190,500],[250,1000],[400,1000],[400,0],[190,0]],1,1,1,1,1)
TooLowFlaps4 = Enveloppe([[0,0],[0,245],[190,245],[190,0]],1,1,1,1,1)
TooLowGear4 = Enveloppe([[0,0],[0,500],[190,500],[190,0]],1,1,1,1,1)

print(TooLowTerrain4.collision([x4,y4]))
print(TooLowFlaps4.collision([x4,y4]))
print(TooLowGear4.collision([x4,y4]))

#Mode 5

x5 = Entree.GlideSlopeDeviation# dots
y5 = Entree.RadioAltitude # ft

GlideSlopeReduced5 = Enveloppe([[1.3,1000],[4,1000],[4,0],[2.98,0],[1.3,150]],1,1,1,1,1)
GlideSlope5 = Enveloppe([[2,300],[4,300],[4,0],[3.68,0],[2,150]],1,1,1,1,1)

print(GlideSlopeReduced5.collision([x5,y5]))
print(GlideSlope5.collision([x5,y5]))

#Mode 6

x6 = Entree.RollAngle # degrees
y6 = Entree.HeightAboveTerrain # ft

ExRollAngle6 = Enveloppe([[10,30],[40,150],[40,500],[90,500],[-90,500],[-40,500],[-40,150],[-10,30]],1,1,1,1,1)

print(ExRollAngle6.collision([x6,y6]))

#Mode 7

Windshear7 = 0



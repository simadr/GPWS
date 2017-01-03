UP = "0"
DOWN = "1"

class Enveloppe():
    def __init__(self, vertexes, alertlevel, priority, flaps, gear, phase):
        self.vertexes = vertexes
        self.alertlevel = alertlevel
        self.priority = priority
        self.flaps = flaps
        self.gear = gear
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
    def have_inside(self, point, flaps, gear):
        if (flaps != self.flaps and self.flaps != None) or (gear != self.gear and self.gear != None): # Si la config n'est pas bonne
            return False
        else:
            return self.collision(point)

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
            return enveloppe_eff[0]

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


Etat0 = Etat(0, 0, 0, 0, 0, 0, 0, 0)

#Mode 1
PullUp1 = Enveloppe([[1750,370],[3000,1000],[6225,2075],[8000,2075],[8000,0],[1750,0]],0,1,None,None,1)
SinkRate1 = Enveloppe([[1750,370],[2610,1180],[5150,2450],[8000,2450],[8000,0],[1750,0]],1,1,None,None,1)
Mode1 = Mode([PullUp1,SinkRate1],None)

x1 = Etat0.VerticalSpeed # ft/mn
y1 = Etat0.RadioAltitude # ft

print(PullUp1.collision([x1,y1]))
print(SinkRate1.collision([x1,y1]))

#Mode 2
PullUp2 = Enveloppe([[2277,220],[3000,790],[8000,790],[8000,0],[2277,0]],0,1,None,1,1)
Terrain2 = Enveloppe([[2277,220],[3000,790],[3900,1500],[6000,1800],[8000,1800],[8000,0],[2277,0]],1,1,1,1,1)
Mode2 = Mode([PulUp2,Terrain2],None)

x2 = Etat0.TerrainClosureRate # ft/mn
y2 = Etat0.RadioAltitude # ft

print(PullUp2.collision([x2,y2]))
print(Terrain2.collision([x2,y2]))

#Mode 3
DontSink = Enveloppe([[0,0],[143,1500],[400,1500],[400,0]],1,1,1,1,1)
Mode3 = Mode([DontSink],"Takeoff")

x3 = Etat0.MSLAltitudeLoss # ft
y3 = Etat0.RadioAltitude # ft

print(DontSink.collision([x3,y3]))

#Mode 4
TooLowTerrain4 = Enveloppe([[190,0],[190,500],[250,1000],[400,1000],[400,0],[190,0]],1,1,1,1,1)
TooLowFlaps4 = Enveloppe([[0,0],[0,245],[190,245],[190,0]],1,1,1,1,1)
TooLowGear4 = Enveloppe([[0,0],[0,500],[190,500],[190,0]],1,1,1,1,1)
Mode4 = Mode([TooLowTerrain4,TooLowFlaps4,TooLowGear4],None)

x4 = Etat0.ComputedAirSpeed # kts
y4 = Etat0.RadioAltitude # ft

print(TooLowTerrain4.collision([x4,y4]))
print(TooLowFlaps4.collision([x4,y4]))
print(TooLowGear4.collision([x4,y4]))

#Mode 5
GlideSlopeReduced5 = Enveloppe([[1.3,1000],[4,1000],[4,0],[2.98,0],[1.3,150]],1,1,1,1,1)
GlideSlope5 = Enveloppe([[2,300],[4,300],[4,0],[3.68,0],[2,150]],1,1,1,1,1)

x5 = Etat0.GlideSlopeDeviation# dots
y5 = Etat0.RadioAltitude # ft

Mode5 = Mode([GlideSlopeReduced5,GlideSlope5],"Approach")

print(GlideSlopeReduced5.collision([x5,y5]))
print(GlideSlope5.collision([x5,y5]))

#Mode 6
ExRollAngle6 = Enveloppe([[10,30],[40,150],[40,500],[90,500],[-90,500],[-40,500],[-40,150],[-10,30]],1,1,1,1,1)
Mode6 = Mode([ExRollAngle])

x6 = Etat0.RollAngle # degrees
y6 = Etat0.HeightAboveTerrain # ft

print(ExRollAngle6.collision([x6,y6]))

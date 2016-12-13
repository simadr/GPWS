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
            print(d)
            if d>0 :
                return False
        return True

class Mode():
    def __init__(self, list_enveloppes):
        self.list_enveloppes = list_enveloppes

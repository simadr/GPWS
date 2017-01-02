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
            print(d)
            if d>0 :
                return False
        return True

    def have_inside(self, point, flaps, gear):
        """
        :param point:
        :param flaps:
        :param gear:
        :return: True si le couple (point, config) se trouve dans l'enveloppe, False sinon
        """
        if (flaps != self.flaps and self.flaps != None) or (gear != self.gear and self.gear != None): # Si la config n'est pas bonne
            return False
        else:
            return self.collision(point)

class Mode():
    def __init__(self, list_enveloppes, phase):
        self.list_enveloppes = list_enveloppes
        self.phase = phase
        self.on = True  #Pour activer/desactiver manuellement un mode

    def get_enveloppe(self, point, flaps, gear):
        """
        :param point:
        :param flaps:
        :param gear:
        :return: L'enveloppe eventuelle dans lequel se trouve le couple (point, config), et None sinon
        """
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
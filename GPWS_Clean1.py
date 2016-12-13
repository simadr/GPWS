
A1 = [0,3]
A2 = [5,3]
A3 = [5,0]
A4 = [0,0]
graphe = [A1,A2,A3,A4]

def collision(graphe,P):
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

print(collision(graphe,[1,6]))
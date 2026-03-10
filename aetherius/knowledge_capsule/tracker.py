from enum import Enum
class Phase(Enum): SPROUT="sprout"; GREEN="green_leaf"; YELLOW="yellow_leaf"; RED="red_leaf"; SOIL="soil"
class KnowledgeCapsule:
    def __init__(self): self.k={}
    def add(self,i,c,p="P2"): self.k[i]={'c':c,'p':p,'conf':0.7,'phase':Phase.SPROUT}
    def access(self,i):
        if i in self.k: self.k[i]['conf']=min(1.0,self.k[i]['conf']+0.03); self.k[i]['phase']=Phase.GREEN if self.k[i]['conf']>=0.8 else Phase.SPROUT; return True
        return False

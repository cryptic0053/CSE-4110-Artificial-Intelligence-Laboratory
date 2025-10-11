# =====================================================
# Quantum Territory Wars — Pygame Edition (UI v2)
# Polished hex UI, hover tooltips, player HUD, action bar,
# turn log, selection/feedback effects, keyboard shortcuts.
# =====================================================

import math, random, heapq, copy, sys, time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Optional

import pygame

# ---------------------------- Window & UI ----------------------------
WIN_W, WIN_H = 1280, 800           # change if you like; UI auto-fits
MARGIN = 16
RIGHT_PANEL_W = 360
FOOTER_H = 110
TOPBAR_H = 64
BG = (16, 18, 23)

# ---------------------------- Colors ----------------------------
WHITE=(250,250,252); GRAY1=(210,212,218); GRAY2=(160,165,176); GRAY3=(110,115,130)
PANEL_BG=(26,28,36); PANEL_STROKE=(70,76,92)
FOCUS=(255,235,120)
DISABLED=(55,58,70)

OWNER_COLORS = {
    0: (90,170,255),   # EXPANSION_EMPIRE (blue)
    1: (255,110,110),  # TECH_COLLECTIVE (red)
    2: (125,220,140),  # ADAPTIVE_ALLIANCE (green)
    3: (95,100,115)    # NEUTRAL (slate)
}
TERRAIN_FILL = {
    "plains": (196,210,178),
    "forest": (86,143,105),
    "mountain": (145,138,133),
    "desert": (233,206,144),
    "water": (102,136,220),
    "quantum_node": (198,168,240),
}
TERRAIN_NAMES = {
    "plains": "Plains",
    "forest": "Forest",
    "mountain": "Mountain",
    "desert": "Desert",
    "water": "Water",
    "quantum_node": "Quantum Node",
}

# ---------------------------- Game Enums ----------------------------
class TerrainType(Enum):
    PLAINS="plains"; FOREST="forest"; MOUNTAIN="mountain"; DESERT="desert"; WATER="water"; QUANTUM_NODE="quantum_node"
class FactionType(Enum):
    EXPANSION_EMPIRE=0; TECH_COLLECTIVE=1; ADAPTIVE_ALLIANCE=2; NEUTRAL=3
class UnitType(Enum):
    SCOUT="scout"; WARRIOR="warrior"; ENGINEER="engineer"; QUANTUM_SPECIALIST="quantum_specialist"

# ---------------------------- Data Classes ----------------------------
@dataclass(frozen=True)
class Position:
    q:int; r:int
    def neighbors(self):
        for dq,dr in [(1,0),(1,-1),(0,-1),(-1,0),(-1,1),(0,1)]:
            yield Position(self.q+dq, self.r+dr)

@dataclass
class Unit:
    unit_type:UnitType; faction:FactionType; position:Position
    health:int; movement_points:int; max_movement:int
    def __post_init__(self):
        if self.health<=0: self.health=self.get_max_health()
        if self.movement_points<=0: self.movement_points=self.max_movement
    def get_max_health(self):
        return {UnitType.SCOUT:50, UnitType.WARRIOR:100, UnitType.ENGINEER:75, UnitType.QUANTUM_SPECIALIST:60}[self.unit_type]

@dataclass
class Hex:
    position:Position; terrain:TerrainType; owner:FactionType; units:List[Unit]; resources:int; quantum_charge:int=0
    def __post_init__(self):
        if self.units is None: self.units=[]

@dataclass
class Player:
    faction:FactionType; resources:int=100; territories_controlled:int=0
    quantum_nodes_controlled:int=0; units:List[Unit]=None; is_ai:bool=True
    def __post_init__(self):
        if self.units is None: self.units=[]

# ---------------------------- A* Pathfinding ----------------------------
class AStar:
    def __init__(self, board): self.board=board
    def dist(self,a:Position,b:Position):
        return max(abs(a.q-b.q), abs((a.q+a.r)-(b.q+b.r)), abs(a.r-b.r))
    def valid(self,p:Position): return p in self.board.hexes
    def neighbors(self,p:Position):
        for n in p.neighbors():
            if self.valid(n): yield n
    def cost(self, frm:Position, to:Position, unit:Unit):
        if not self.valid(to): return 9e9
        h=self.board.hexes[to]
        base={
            TerrainType.PLAINS:1.0, TerrainType.FOREST:1.5, TerrainType.MOUNTAIN:2.0,
            TerrainType.DESERT:1.3, TerrainType.WATER:3.0, TerrainType.QUANTUM_NODE:1.0
        }[h.terrain]
        if unit.unit_type==UnitType.SCOUT: base*=0.8
        if unit.unit_type==UnitType.ENGINEER and h.terrain==TerrainType.MOUNTAIN: base*=0.7
        if h.owner not in (FactionType.NEUTRAL, unit.faction): base*=1.5
        return base
    def path(self,start:Position,goal:Position,unit:Unit):
        if start==goal: return [start]
        cnt=0; openh=[(0,cnt,start,[start])]; g={start:0.0}; closed=set()
        while openh:
            _,_,cur,pth=heapq.heappop(openh)
            if cur in closed: continue
            if cur==goal: return pth
            closed.add(cur)
            for nb in self.neighbors(cur):
                if nb in closed: continue
                tg=g[cur]+self.cost(cur,nb,unit)
                if nb not in g or tg<g[nb]:
                    g[nb]=tg; cnt+=1
                    heapq.heappush(openh,(tg+self.dist(nb,goal),cnt,nb,pth+[nb]))
        return []

# ---------------------------- Minimax AI (kept compact) ----------------------------
class GameState:
    def __init__(self,board,players,idx,turn):
        self.board=board; self.players=players; self.idx=idx; self.turn=turn
    def copy(self): return GameState(copy.deepcopy(self.board), copy.deepcopy(self.players), self.idx, self.turn)

class MinimaxAI:
    def __init__(self,faction,depth=2): self.faction=faction; self.depth=depth
    def eval(self,st:GameState):
        me=next((p for p in st.players if p.faction==self.faction),None)
        if not me: return -1e6
        opp=[p for p in st.players if p.faction!=self.faction]
        sc=0.0
        terr=me.territories_controlled*20; max_ot=max((p.territories_controlled for p in opp), default=0)
        sc+=(terr - max_ot*10)*0.45
        adv=me.resources-(sum(p.resources for p in opp)/len(opp) if opp else 0)
        sc+=adv*0.12
        q=me.quantum_nodes_controlled*50; max_oq=max((p.quantum_nodes_controlled for p in opp), default=0)
        sc+=(q - max_oq*25)*0.2
        mil=len(me.units)*10 - (sum(len(p.units) for p in opp)/max(1,len(opp)))*5
        sc+=mil*0.1
        return sc
    def moves(self,st):
        p=st.players[st.idx]; m=[]
        if p.resources>=30: m.append(("expand",30))
        if p.resources>=40: m.append(("build",40))
        if p.resources>=25: m.append(("economy",25))
        if not m: m.append(("end",0))
        return m
    def apply(self,st,mv):
        ns=st.copy(); p=ns.players[ns.idx]; act,cost=mv
        if act=="expand" and p.resources>=cost:
            p.resources-=cost
            owned=[h for h in ns.board.hexes.values() if h.owner==p.faction]; random.shuffle(owned)
            claimed=False
            for oh in owned:
                for nb in oh.position.neighbors():
                    if nb in ns.board.hexes and ns.board.hexes[nb].owner==FactionType.NEUTRAL:
                        ns.board.hexes[nb].owner=p.faction; p.territories_controlled+=1
                        if ns.board.hexes[nb].terrain==TerrainType.QUANTUM_NODE or random.random()<0.1:
                            p.quantum_nodes_controlled+=1
                        claimed=True; break
                if claimed: break
            if not claimed: p.territories_controlled+=1
        elif act=="build" and p.resources>=cost:
            p.resources-=cost
            pos=None
            for h in ns.board.hexes.values():
                if h.owner==p.faction: pos=h.position; break
            if pos is None: pos=next(iter(ns.board.hexes))
            u=Unit(UnitType.WARRIOR,p.faction,pos,100,2,2)
            p.units.append(u); ns.board.hexes[pos].units.append(u)
        elif act=="economy" and p.resources>=cost:
            p.resources-=cost; p.resources+=40
        return ns
    def minimax(self,st,d,a,b,maxing):
        if d==0: return self.eval(st), None
        best_mv=None
        if maxing:
            best=-1e9
            for mv in self.moves(st):
                ns=self.apply(st,mv); ns.idx=(ns.idx+1)%len(ns.players)
                val,_=self.minimax(ns,d-1,a,b,False)
                if val>best: best,val_mv=val,mv; best_mv=mv
                a=max(a,val)
                if b<=a: break
            return best_mv and best or -1e9, best_mv
        else:
            worst=1e9
            for mv in self.moves(st):
                ns=self.apply(st,mv); ns.idx=(ns.idx+1)%len(ns.players)
                val,_=self.minimax(ns,d-1,a,b,True)
                if val<worst: worst,val_mv=val,mv; best_mv=mv
                b=min(b,val)
                if b<=a: break
            return best_mv and worst or 1e9, best_mv
    def best(self,st):
        _,mv=self.minimax(st,self.depth,-1e9,1e9,True)
        return mv or ("end",0)

# ---------------------------- Board & Game ----------------------------
class GameBoard:
    def __init__(self,size=11):
        self.size=size; self.hexes:Dict[Position,Hex]={}; self.astar=AStar(self); self.qnodes=[]
        self._gen()
    def _gen(self):
        for q in range(self.size):
            for r in range(self.size-q):
                pos=Position(q,r)
                terr=self._terrain()
                hx=Hex(pos,terr,FactionType.NEUTRAL,[],random.randint(5,25))
                self.hexes[pos]=hx
                if terr==TerrainType.QUANTUM_NODE: self.qnodes.append(pos)
    def _terrain(self):
        if len(self.qnodes)<7 and random.random()<0.06: return TerrainType.QUANTUM_NODE
        p=random.random()
        if p<0.4: return TerrainType.PLAINS
        if p<0.6: return TerrainType.FOREST
        if p<0.75: return TerrainType.MOUNTAIN
        if p<0.9: return TerrainType.DESERT
        return TerrainType.WATER

class Game:
    def __init__(self, player_types):
        self.board=GameBoard(size=11)
        self.players:List[Player]=[]
        self.idx=0; self.turn=1
        self.game_over=False; self.winner=None
        self.ai={}
        facs=[FactionType.EXPANSION_EMPIRE, FactionType.TECH_COLLECTIVE, FactionType.ADAPTIVE_ALLIANCE]
        for i,is_ai in enumerate(player_types):
            p=Player(faction=facs[i], is_ai=is_ai); self.players.append(p)
            if is_ai: self.ai[facs[i]]=MinimaxAI(facs[i],depth=2)
        self._setup()
        self.log:List[str]=[]
        self.last_action_feedback=None  # (center_xy, ttl)

    def _setup(self):
        starts=[Position(2,2), Position(self.board.size-3,2), Position(self.board.size//2, self.board.size//2-2)]
        for i,p in enumerate(self.players):
            pos=starts[i]
            self.board.hexes[pos].owner=p.faction
            p.territories_controlled+=1
            u=Unit(UnitType.SCOUT,p.faction,pos,50,3,3)
            p.units.append(u); self.board.hexes[pos].units.append(u)

    def post(self, msg:str):
        self.log.append(msg)
        if len(self.log)>6: self.log=self.log[-6:]

    def affordable(self,cost): return self.players[self.idx].resources>=cost

    def income_tick(self):
        for p in self.players: p.resources += 10 + p.territories_controlled*2

    def check_victory(self):
        for p in self.players:
            if p.territories_controlled>=18: self.game_over=True; self.winner=p.faction; self.post(f"{p.faction.name} wins (Territory)!"); return
            if p.quantum_nodes_controlled>=5: self.game_over=True; self.winner=p.faction; self.post(f"{p.faction.name} wins (Quantum)!"); return
            if p.resources>=600: self.game_over=True; self.winner=p.faction; self.post(f"{p.faction.name} wins (Economy)!"); return

    def available(self):
        p=self.players[self.idx]; opts=[]
        if p.resources>=30: opts.append(("Expand", "expand",30))
        if p.resources>=40: opts.append(("Build", "build",40))
        if p.resources>=25: opts.append(("Economy","economy",25))
        opts.append(("End Turn","end",0))
        return opts

    def apply(self, act:str, cost:int):
        p=self.players[self.idx]
        if act=="expand" and p.resources>=cost:
            p.resources-=cost
            owned=[h for h in self.board.hexes.values() if h.owner==p.faction]; random.shuffle(owned)
            claimed=None
            for oh in owned:
                for nb in oh.position.neighbors():
                    if nb in self.board.hexes and self.board.hexes[nb].owner==FactionType.NEUTRAL:
                        self.board.hexes[nb].owner=p.faction; p.territories_controlled+=1
                        if self.board.hexes[nb].terrain==TerrainType.QUANTUM_NODE or random.random()<0.1:
                            p.quantum_nodes_controlled+=1
                        claimed=nb; break
                if claimed: break
            if not claimed: p.territories_controlled+=1
            self.post(f"{p.faction.name}: Expand")
            return claimed
        elif act=="build" and p.resources>=cost:
            p.resources-=cost
            spawn=None
            for h in self.board.hexes.values():
                if h.owner==p.faction: spawn=h.position; break
            if spawn is None: spawn=next(iter(self.board.hexes))
            u=Unit(UnitType.WARRIOR,p.faction,spawn,100,2,2)
            p.units.append(u); self.board.hexes[spawn].units.append(u)
            self.post(f"{p.faction.name}: Build")
            return spawn
        elif act=="economy" and p.resources>=cost:
            p.resources-=cost; p.resources+=40
            self.post(f"{p.faction.name}: Economy")
            return None
        elif act=="end":
            self.post(f"{p.faction.name}: End Turn")
            return None
        return None

    def next_turn(self):
        self.idx=(self.idx+1)%len(self.players)
        if self.idx==0:
            self.turn+=1
            self.income_tick()

# ---------------------------- Pygame UI helpers ----------------------------
def fit_hex_size():
    """Compute a hex size that fits the available map area."""
    usable_w = WIN_W - RIGHT_PANEL_W - MARGIN*3
    usable_h = WIN_H - FOOTER_H - TOPBAR_H - MARGIN*3
    # rough triangle width ~ sqrt(3)/2 * (2*size) * board_w
    # we’ll pick a size that allows an 11-row triangular board nicely.
    base = min(usable_w/ (math.sqrt(3)*(11+4)), usable_h/ (1.6*(11+3)))
    return max(20, int(base))

HEX_SIZE = fit_hex_size()
def axial_to_pixel(q,r, origin):
    x = HEX_SIZE*(math.sqrt(3)*q + math.sqrt(3)/2*r)
    y = HEX_SIZE*(1.5*r)
    return int(origin[0]+x), int(origin[1]+y)

def hex_corners(center):
    cx,cy=center; pts=[]
    for i in range(6):
        ang=math.radians(60*i-30)
        pts.append((int(cx+HEX_SIZE*math.cos(ang)), int(cy+HEX_SIZE*math.sin(ang))))
    return pts

def point_in_poly(pt,poly):
    x,y=pt; inside=False; j=len(poly)-1
    for i in range(len(poly)):
        xi,yi=poly[i]; xj,yj=poly[j]
        if ((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/(yj-yi+1e-9)+xi): inside=not inside
        j=i
    return inside

class Button:
    def __init__(self, rect, label, hotkey:str, action:str, cost:int):
        self.r=pygame.Rect(rect); self.label=label; self.hotkey=hotkey
        self.action=action; self.cost=cost; self.enabled=True
    def draw(self,surf,font):
        col=(40,45,58) if self.enabled else DISABLED
        pygame.draw.rect(surf,col,self.r,border_radius=10)
        pygame.draw.rect(surf,(90,96,112),self.r,2,border_radius=10)
        t = f"{self.label} [{self.hotkey}]"
        if self.cost>0: t+=f"  -{self.cost}"
        lbl=font.render(t, True, WHITE if self.enabled else GRAY3)
        surf.blit(lbl,(self.r.x+12,self.r.y+10))
    def hit(self,pos): return self.enabled and self.r.collidepoint(pos)

# ---------------------------- Main (UI Loop) ----------------------------
def choose_mode(screen,font_big,font):
    screen.fill(BG)
    title=font_big.render("Quantum Territory Wars",True,WHITE); screen.blit(title,(MARGIN, MARGIN))
    opts=[("1 Human & 2 AI",[False,True,True]), ("2 Humans & 1 AI",[False,False,True]), ("3 Humans",[False,False,False])]
    rects=[]
    y=140
    for txt,mode in opts:
        r=pygame.Rect(MARGIN,y,420,64)
        pygame.draw.rect(screen,(38,42,55),r,border_radius=12)
        pygame.draw.rect(screen,(92,100,118),r,2,border_radius=12)
        screen.blit(font.render(txt,True,WHITE),(r.x+16,r.y+18))
        rects.append((r,mode)); y+=84
    pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit(0)
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                if any(r.collidepoint(e.pos) for r,_ in rects):
                    for r,m in rects:
                        if r.collidepoint(e.pos): return m

def run():
    pygame.init()
    screen=pygame.display.set_mode((WIN_W,WIN_H))
    pygame.display.set_caption("Quantum Territory Wars — UI v2")
    clock=pygame.time.Clock()
    font=pygame.font.SysFont("consolas",18)
    font_mid=pygame.font.SysFont("consolas",20, bold=True)
    font_big=pygame.font.SysFont("consolas",28, bold=True)

    mode=choose_mode(screen,font_big,font_mid)
    game=Game(mode)

    # Layout
    MAP_ORIGIN=(MARGIN+HEX_SIZE*2, TOPBAR_H+MARGIN+HEX_SIZE)  # some padding
    footer_rect=pygame.Rect(0, WIN_H-FOOTER_H, WIN_W, FOOTER_H)
    right_rect=pygame.Rect(WIN_W-RIGHT_PANEL_W-MARGIN, TOPBAR_H+MARGIN, RIGHT_PANEL_W, WIN_H-FOOTER_H-TOPBAR_H-2*MARGIN)

    # Buttons
    btns=[
        Button((MARGIN, WIN_H-FOOTER_H+20, 200, 56), "Expand","E","expand",30),
        Button((MARGIN+220, WIN_H-FOOTER_H+20, 200, 56), "Build","B","build",40),
        Button((MARGIN+440, WIN_H-FOOTER_H+20, 200, 56), "Economy","C","economy",25),
        Button((MARGIN+660, WIN_H-FOOTER_H+20, 200, 56), "End Turn","SPACE","end",0),
    ]
    hotkey_map={'e':"expand",'b':"build",'c':"economy"}
    # precompute hex centers for hit-testing
    hex_centers={pos:axial_to_pixel(pos.q,pos.r,MAP_ORIGIN) for pos in game.board.hexes}

    selected:Optional[Position]=None

    def hex_at(pos):
        for p,ctr in hex_centers.items():
            if point_in_poly(pos, hex_corners(ctr)):
                return p
        return None

    def draw_topbar():
        pygame.draw.rect(screen,BG,(0,0,WIN_W,TOPBAR_H))
        title=font_big.render(f"Quantum Territory Wars   |   Turn {game.turn}", True, WHITE)
        screen.blit(title,(MARGIN, TOPBAR_H//2 - title.get_height()//2))

    def draw_map():
        # subtle drop shadow pass
        for pos,hx in game.board.hexes.items():
            c=hex_centers[pos]; pts=hex_corners((c[0]+2,c[1]+2))
            pygame.draw.polygon(screen,(0,0,0,20),pts)

        # fill & borders
        for pos,hx in game.board.hexes.items():
            c=hex_centers[pos]; pts=hex_corners(c)
            fill=TERRAIN_FILL[hx.terrain.value]
            pygame.draw.polygon(screen, fill, pts)
            rim=OWNER_COLORS[hx.owner.value]
            pygame.draw.polygon(screen, rim, pts, 3)
            # quantum glyph
            if hx.terrain==TerrainType.QUANTUM_NODE:
                pygame.draw.circle(screen,(250,236,255),c,6); pygame.draw.circle(screen,(120,85,180),c,6,2)

        # units
        for p in game.players:
            uc=OWNER_COLORS[p.faction.value]
            for u in p.units:
                c=hex_centers[u.position]
                pygame.draw.circle(screen, uc, c, 8)
                pygame.draw.circle(screen, (30,30,32), c, 8, 2)

        # selection & last action pulse
        if selected and selected in hex_centers:
            pygame.draw.polygon(screen, FOCUS, hex_corners(hex_centers[selected]), 2)
        if game.last_action_feedback:
            (cx,cy),ttl=game.last_action_feedback
            alpha=int(180* ttl/0.5)
            r=int(14 + (1-ttl/0.5)*10)
            s=pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(s,(255,240,150,alpha),(r+2,r+2),r,2)
            screen.blit(s,(cx-r-2, cy-r-2))
            ttl-=clock.get_time()/1000.0
            if ttl<=0: game.last_action_feedback=None
            else: game.last_action_feedback=((cx,cy),ttl)

    def draw_right():
        pygame.draw.rect(screen,PANEL_BG,right_rect,border_radius=12)
        pygame.draw.rect(screen,PANEL_STROKE,right_rect,2,border_radius=12)
        x=right_rect.x+14; y=right_rect.y+12

        # Player cards
        for i,p in enumerate(game.players):
            is_now = (i==game.idx)
            card=pygame.Rect(x, y, right_rect.w-28, 74)
            pygame.draw.rect(screen,(34,36,46),card,border_radius=10)
            pygame.draw.rect(screen,(90,96,112),card,2,border_radius=10)
            if is_now:
                glow=pygame.Surface((card.w,card.h), pygame.SRCALPHA)
                pygame.draw.rect(glow,(255,235,140,50), glow.get_rect(), border_radius=10)
                screen.blit(glow,(card.x,card.y))
            name=f"{p.faction.name}  [{'AI' if p.is_ai else 'HUMAN'}]"
            lbl=font_mid.render(name, True, OWNER_COLORS[p.faction.value]); screen.blit(lbl,(card.x+10, card.y+8))
            sub=f"Terr:{p.territories_controlled}   Res:{p.resources}   Units:{len(p.units)}   QN:{p.quantum_nodes_controlled}"
            screen.blit(font.render(sub, True, GRAY1), (card.x+10, card.y+38))
            y+=card.h+10

        # Turn log
        y+=8
        screen.blit(font_mid.render("Turn Log",True,WHITE),(x,y)); y+=28
        for m in game.log[::-1]:
            screen.blit(font.render("• "+m,True,GRY1 if (GRY1:=GRAY1) else GRAY1),(x,y)); y+=22

    def draw_footer():
        pygame.draw.rect(screen,(22,24,30),footer_rect)
        pygame.draw.rect(screen,(78,86,104),footer_rect,2)
        # enable/disable
        cur=game.players[game.idx]
        is_human=not cur.is_ai and not game.game_over
        for b in btns:
            if not is_human: b.enabled=False
            else:
                if b.action=="end": b.enabled=True
                elif b.action=="expand": b.enabled=game.affordable(30)
                elif b.action=="build": b.enabled=game.affordable(40)
                elif b.action=="economy": b.enabled=game.affordable(25)
            b.draw(screen,font_mid)

        # hover tooltip
        mx,my=pygame.mouse.get_pos()
        if my < WIN_H-FOOTER_H and not game.game_over:
            hp = hex_at((mx,my))
            if hp:
                hx=game.board.hexes[hp]
                tip=f"{TERRAIN_NAMES[hx.terrain.value]}  |  Owner: {hx.owner.name}  |  Res:{hx.resources}  |  Units:{len(hx.units)}"
                ts=font.render(tip, True, WHITE)
                tw,th=ts.get_size()
                pad=8
                box=pygame.Rect(mx+12,my+12,tw+pad*2,th+pad*2)
                pygame.draw.rect(screen,(32,34,44),box,border_radius=8)
                pygame.draw.rect(screen,(88,94,112),box,2,border_radius=8)
                screen.blit(ts,(box.x+pad, box.y+pad))

    # ----------- Main loop -----------
    AI_DELAY = 240  # ms pause so you can see AI actions
    last_ai_time = 0

    running=True
    while running:
        dt=clock.tick(60)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
            elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                if game.game_over: break
                mx,my=e.pos
                # click on map selects
                if my < WIN_H-FOOTER_H:
                    hp=hex_at((mx,my))
                    if hp: selected=hp
                # click buttons
                if footer_rect.collidepoint((mx,my)):
                    cur=game.players[game.idx]
                    if not cur.is_ai and not game.game_over:
                        for b in btns:
                            if b.hit((mx,my)):
                                pos=game.apply(b.action,b.cost)
                                if pos and pos in hex_centers:
                                    game.last_action_feedback=(hex_centers[pos],0.5)
                                game.check_victory()
                                if not game.game_over:
                                    game.next_turn()
                                break
            elif e.type==pygame.KEYDOWN and not game.game_over:
                cur=game.players[game.idx]
                # keyboard shortcuts
                if not cur.is_ai:
                    if e.key==pygame.K_e: act="expand"
                    elif e.key==pygame.K_b: act="build"
                    elif e.key==pygame.K_c: act="economy"
                    elif e.key==pygame.K_SPACE: act="end"
                    else: act=None
                    if act:
                        cost={"expand":30,"build":40,"economy":25,"end":0}[act]
                        pos=game.apply(act,cost)
                        if pos and pos in hex_centers: game.last_action_feedback=(hex_centers[pos],0.5)
                        game.check_victory()
                        if not game.game_over: game.next_turn()

        # AI auto-turn with small delay
        if not game.game_over and game.players[game.idx].is_ai:
            if pygame.time.get_ticks() - last_ai_time > AI_DELAY:
                p=game.players[game.idx]
                st=GameState(game.board, game.players, game.idx, game.turn)
                mv=game.ai[p.faction].best(st)
                pos=game.apply(mv[0], mv[1])
                if pos and pos in hex_centers: game.last_action_feedback=(hex_centers[pos],0.5)
                game.check_victory()
                if not game.game_over: game.next_turn()
                last_ai_time = pygame.time.get_ticks()

        # Draw
        screen.fill(BG)
        draw_topbar()
        draw_map()
        draw_right()
        draw_footer()

        # Winner banner
        if game.game_over:
            msg=f"WINNER: {game.winner.name}" if game.winner else "Draw"
            s=font_big.render(msg,True,FOCUS)
            screen.blit(s,(WIN_W//2 - s.get_width()//2, TOPBAR_H//2 - s.get_height()//2))

        pygame.display.flip()

    pygame.quit()

if __name__=="__main__":
    run()

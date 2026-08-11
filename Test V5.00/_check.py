"""Verification statique du composant : equilibrage, identifiants, code mort."""
import io, os, re, sys

# Resolu depuis ce fichier : le script est versionne et doit tourner ailleurs
# que sur la machine de l'auteur.
D = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "modules", "apps", "Tacho2")
BT = chr(96)


def strip_js(src):
    """Retire commentaires et chaines par automate -- une regex sur les
    template literals est trop fragile ici."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            i = src.find("*/", i + 2)
            i = n if i < 0 else i + 2
        elif c in ('"', "'", BT):
            q = c
            i += 1
            while i < n and src[i] != q:
                i += 2 if src[i] == "\\" else 1
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


t = io.open(D + r"\tacho.vue", encoding="utf-8").read()
tpl = t[t.index("<template>"):t.index("</template>")]
scr = t[t.index("<script setup>") + 14:t.index("</script>")]
clean = strip_js(scr)

ok = True
print("=== equilibrage du script (chaines et commentaires retires) ===")
for o, f, nom in (("{", "}", "accolades"), ("(", ")", "parentheses"), ("[", "]", "crochets")):
    a, b = clean.count(o), clean.count(f)
    good = a == b
    ok = ok and good
    print("  %-12s %4d / %-4d %s" % (nom, a, b, "OK" if good else "<<< DESEQUILIBRE"))

print("\n=== identifiants du template definis dans le script ===")
used = set(re.findall(r'(?<![\w-])[:@][\w.-]+="\s*([A-Za-z_$][\w$]*)', tpl))
used |= set(re.findall(r'v-show="\s*([A-Za-z_$][\w$]*)', tpl))
used |= set(re.findall(r"\{\{\s*([A-Za-z_$][\w$]*)", tpl))
defined = set(re.findall(r"(?:function|const|let|var)\s+([A-Za-z_$][\w$]*)", scr))
BUILTIN = {"true", "false", "undefined", "null", "Math", "Number", "String", "Object", "u", "k", "el"}
missing = sorted(used - defined - BUILTIN)
ok = ok and not missing
print("  %d references | manquantes : %s" % (len(used), missing or "aucune"))

print("\n=== helpers : definis / appeles ===")
for h in ("inputArc", "arcLen", "arcPath", "arcPoint", "iconTf",
          "clamp01", "etSet", "fitSize", "sty", "unitSty", "capSty", "resetTrip",
          "etLoadPercent", "etDamagePercent", "setU",
          # Les caches ajoutes par la passe de perf. Un cache calcule et jamais
          # lu est exactement la regression que ce controle doit voir.
          "styles", "unitStyles", "iconTfs", "inputArcs"):
    d = bool(re.search(r"(?:function|const)\s+%s\b" % h, scr))
    # Toute mention hors definition compte comme un usage : un helper s'appelle
    # avec des parentheses, mais un cache se lit en propriete (styles.gear) et
    # une liaison peut etre nue (@dblclick="resetTrip"). Ne compter que les
    # parentheses signalait ces deux formes comme du code mort.
    calls = len(re.findall(r"\b%s\b" % h, clean + tpl)) - (1 if d else 0)
    flag = ""
    if d and calls == 0:
        flag = "<<< CODE MORT"
        ok = False
    elif not d and calls > 0:
        flag = "<<< APPELE MAIS ABSENT"
        ok = False
    if d or calls:
        print("  %-16s defini=%-5s appels=%-3d %s" % (h, d, calls, flag))

print("\n=== imports vue ===")
m = re.search(r'import \{([^}]*)\} from "vue"', scr)
for i in [x.strip() for x in m.group(1).split(",")]:
    c = len(re.findall(r"\b%s\s*\(" % i, clean))
    if c == 0:
        ok = False
    print("  %-10s %d usages %s" % (i, c, "<<< INUTILISE" if c == 0 else ""))

print("\n=== cout par render : appels de style dans le template ===")
for fn in ("sty", "unitSty", "capSty", "arcPoint", "iconTf", "inputArc", "arcLen"):
    print("  %-10s %d" % (fn, len(re.findall(r"\b%s\s*\(" % fn, tpl))))

print("\n->", "VALIDE" if ok else "PROBLEME")
sys.exit(0 if ok else 1)

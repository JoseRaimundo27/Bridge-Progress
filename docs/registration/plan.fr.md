# Module II.2 — Recalage OBBP-ICP : ce que nous allons faire

**Équipe :** Oscar et Gabriel · **Branche :** `bridge-segmentation` · **Mis à jour le :** 8 octobre 2026
**English version:** [plan.en.md](plan.en.md)

Ce document résume le travail prévu sur le Module II.2. Le détail de chaque tâche (mission, fichiers, résultat attendu) est dans Jira. Les chiffres cités viennent de l'[analyse initiale](analyse-initiale.fr.md).

---

## 1. Objectif

Aligner le nuage **as-built** du pont (scan de drone, déjà nettoyé par RandLA-Net) sur le nuage **as-planned** produit à partir du BIM.

Le module produit :
- le **scan recalé** ;
- la **matrice de transformation** 4×4 ;
- la **distance moyenne `D_avg`**, que le Module III utilise pour fixer son seuil `O_thr = D_avg + C`.

**Référence :** Tang & Shi (2026), section *Module II*, Algorithme 1 (Fig. 4), Tableaux 1 et 2, Fig. 10.

## 2. Entrées et sorties

| Sens | Avec qui | Donnée |
|---|---|---|
| Entrée | Module I (BIM) | Nuage as-planned `.ply`, en mètres, à **densité uniforme** |
| Entrée | Module II.1 (RandLA-Net) | Scan as-built `.ply` contenant uniquement le pont |
| Sortie | Module III | `scan_registered.ply`, `transform.json`, `metrics.json` (avec `D_avg`) |

## 3. Organisation du code

```
ModuleTwo Registration/
├── AsBuilt/  AsPlanned/        # données d'entrée (non versionnées)
├── outputs/                    # résultats (non versionnés)
└── Python/
    ├── run_registration.py     # point d'entrée : charge → register() → sauvegarde
    ├── inspect_clouds.py       # fiche données (T0.3)
    ├── benchmark_rotations.py  # robustesse aux rotations (T3.2)
    ├── registration/           # le code du module, une fonction par étape
    ├── tests/                  # tests pytest sur ponts synthétiques
    └── legacy/obbp_icp_v0.py   # ancien script, à supprimer à la fin
```

Chaque fonction à écrire lève `NotImplementedError("Tx.y")`, où `Tx.y` est la tâche Jira correspondante. Les tests à activer sont marqués `skip(reason="Tx.y")`.

## 4. Avant de commencer

L'analyse du 8 octobre a montré trois choses à régler d'abord (deux sont faites) :

| Action | Qui | Pourquoi |
|---|---|---|
| ✅ Récupérer les commits de Gabriel et intégrer les corrections du 2 octobre (Modules I et II.1) | Oscar | Fait le 8 octobre ([analyse §2](analyse-initiale.fr.md#2-état-du-dépôt-et-intégration)) |
| Régénérer le nuage as-planned avec une densité uniforme | Oscar | Avec 2000 points par élément, le recalage échoue à chaque fois (E8). À faire avec les vrais modèles IFC |
| ✅ Configurer l'identité git | Oscar | Fait le 8 octobre |

## 5. Les tâches

Taille : **S** ≈ ½ journée · **M** ≈ 1–2 jours · **L** ≈ 3–5 jours.
Priorité après analyse : 🔴 haute · 🟠 normale · 🟡 selon les données (T0.3).

**Répartition actuelle (8 octobre) :** Oscar prend toutes les tâches pour l'instant. Les colonnes « Qui » (A / B) gardent la répartition prévue dans Jira pour plus tard.

### Phase 0 — Mise en place

| Tâche | Taille | Qui | Priorité | Ce qui est attendu |
|---|---|---|---|---|
| T0.1 Données et baseline | S | Ensemble | 🔴 | Baseline sur D19 : `D_avg`, matrice, temps, captures. Vérifier visuellement que le résultat n'est pas à l'envers |
| T0.2 Nettoyage du dossier | S | A | ✅ fait | — |
| T0.3 Fiche données | M | B | 🔴 | Tableau pour D19 et S07. **Ajouts suite à l'analyse :** densité du BIM par élément, float32 ou float64, une dimension connue pour vérifier l'échelle |

### Phase 1 — Corriger et fiabiliser l'algorithme

| Tâche | Taille | Qui | Priorité | Ce qui est attendu |
|---|---|---|---|---|
| T1.1 Refactorisation | M | A | 🔴 | Une fonction par étape. Même résultat que la baseline avec les anciens paramètres |
| T1.2 Recentrage | S | A | 🟡 | Offset commun en float64. Moins urgent : Open3D calcule déjà en float64 (E3) |
| T1.3 Axes en XY (PCA 2D) | M | A | 🟠 | Angle retrouvé à ±1°, plus de NaN. Le prototype atteint < 0,3° (E9) |
| T1.4 Mise à niveau Z | M | A | 🟡 | Seulement si T0.3 montre une inclinaison de plus de ~10° (E4) |
| T1.5 ICP multi-échelle et choix du candidat | M | B | 🔴 | Plus aucun recalage à l'envers. Le prototype : 8/8 (E12) |
| T1.6 Point-to-plane | S | B | 🟠 | Tableau comparatif. Point-to-plane est 2× plus rapide sur les ponts synthétiques (E10) |
| T1.7 Échelle | S | B | 🟡 | Seulement si T0.3 trouve une erreur d'échelle. 2 % suffisent à fausser le résultat (E6) |
| **T1.8 Contrôle d'échec** *(proposée)* | S | à décider | 🟠 | Avertir quand le recalage est douteux, au lieu d'annoncer un succès |

### Phase 2 — Entrées, sorties et intégration

| Tâche | Taille | Qui | Priorité | Ce qui est attendu |
|---|---|---|---|---|
| T2.1 Arguments et chemins | S | A | 🟠 | `make m2-2` et la ligne de commande sans modifier le code. `--viz` désactivé par défaut (sinon blocage sans écran) |
| T2.2 Export pour le Module III | S | A | 🟠 | `scan_registered.ply`, `transform.json`, `metrics.json` à chaque exécution |
| T2.3 Métriques | M | B | 🟠 | Médiane, 95e percentile, distance BIM→scan, carte de chaleur. Discuter de `D_avg` avec le Module III (E11) |

### Phase 3 — Validation

| Tâche | Taille | Qui | Priorité | Ce qui est attendu |
|---|---|---|---|---|
| T3.1 Tests synthétiques | M | A | 🟠 | Tous les tests passent ; erreur < 0,5° et < 2 × voxel |
| T3.2 Banc d'essai rotations | L | B | 🟠 | Tableau comme le Tableau 2 du papier. Réussite mesurée par rapport à la transformation connue |
| T3.3 Effet de la segmentation | M | B | 🟠 | Tableau comme le Tableau 1 du papier (brut / manuel / RandLA-Net). Avec 22 % de points parasites laissés par RandLA-Net, OBBP-ICP échoue 4/4 sur synthétique (analyse §5) |
| T3.4 Pont partiel | L | Ensemble | 🔴 **à avancer** | Cas normal pendant la construction : 0/12 réussites aujourd'hui, 10/12 avec FPFH + RANSAC (E5). FPFH + RANSAC rattrape aussi la sortie bruitée de RandLA-Net (§5) |
| T3.5 Deuxième pont (S07) | S | Ensemble | 🟠 | Mêmes métriques que D19, sans changer les paramètres |

### Phase 4 — Livraison

| Tâche | Taille | Qui | Ce qui est attendu |
|---|---|---|---|
| T4.1 Documentation et PR | S | Ensemble | README du module, docstrings, PR `bridge-segmentation` → `main` avec les résultats de T3.2 et T3.3 |

## 6. Ordre de travail

```
Avant de commencer (intégration, nuage BIM régénéré)
        │
T0.1 → T0.3 ─┬─► T1.1 ─► T1.3 ─► T1.2 ─► (T1.4) ──────────────┐
             │                                                 ├─► T2.1 ─► T2.2 ─► T3.1 ─► T3.2 ─► T3.5 ─► T4.1
             └─► T1.5 ─► T1.8 ─► T1.6 ─► (T1.7) ─► T2.3 ───────┤
                                                               │
             T3.4 (stratégie FPFH + RANSAC), dès la fin de T1.1 ┤
             T3.3 (dès que l'équipe II.1 fournit le scan RandLA-Net) ┘
```

**Changements par rapport au plan initial :**
- T3.4 commence plus tôt : c'est le principal risque du module.
- T1.2 passe après T1.3 : elle est moins urgente.
- T1.8 est ajoutée.

**Règle importante :** T1.1 crée le contenu de tous les fichiers du paquet. Elle doit être **fusionnée avant** que la personne B travaille sur `fine_alignment.py` (T1.5), sinon il y aura des conflits.

## 7. Méthode de travail

- **Une tâche = un ou plusieurs commits** dont le message cite la tâche, par exemple `feat(T1.3): main axes by 2D PCA`.
- **Avant de pousser :**
  - les tests passent : `cd "ModuleTwo Registration/Python" && python -m pytest tests` ;
  - le binôme a relu le code.
- **À la fin de chaque tâche :**
  - une ligne dans le [suivi des modifications](../suivi-des-modifications.md), avec le résultat mesuré ;
  - une ligne dans le [journal de bord](../journal-de-bord.md) ;
  - le statut mis à jour dans Jira.
- **Mesurer avant et après :** chaque amélioration est comparée à la baseline (T0.1) ou aux résultats de l'[analyse initiale](analyse-initiale.fr.md).

## 8. Quand une tâche est-elle terminée ?

1. Le code est écrit, sans `NotImplementedError` restant pour cette tâche.
2. Les tests de la tâche sont activés (sans `skip`) et passent.
3. Le résultat est mesuré et noté dans le suivi.
4. Le binôme a relu le code.

## 9. Vocabulaire

| Terme | Sens |
|---|---|
| As-built | Ce qui est réellement construit : le scan du chantier |
| As-planned | Ce qui est prévu : le nuage généré à partir du BIM |
| Recalage | Trouver le déplacement (rotation + translation) qui superpose le scan au BIM |
| OBB | Boîte englobante orientée : donne l'axe long du pont pour un premier alignement |
| ICP | Algorithme qui affine l'alignement en rapprochant chaque point de son plus proche voisin |
| `fitness` | Part des points du scan qui ont un voisin dans le BIM à moins du seuil |
| RMSE | Erreur quadratique moyenne des points appariés |
| `D_avg` | Distance moyenne de chaque point du scan au point du BIM le plus proche |
| FPFH + RANSAC | Alignement par descripteurs géométriques locaux, robuste aux nuages partiels |
| Voxel | Cube de la grille utilisée pour sous-échantillonner le nuage |

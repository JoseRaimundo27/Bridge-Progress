# Suivi des modifications — Bridge-Progress

Registre de toutes les améliorations et modifications du projet, pour garder une trace de ce qui a été changé, pourquoi, et avec quel résultat mesuré. Il sert de base au rapport de stage.

- Le travail jour par jour est dans le [journal de bord](journal-de-bord.md).
- Une modification importante a son propre document détaillé (avant/après, tests), lié dans la colonne « Détail ».

**Comment le remplir :** une ligne par modification (un commit ou un groupe de commits cohérent). Le statut est `non commité`, `commité <hash>`, `poussé`, ou `fusionné dans main`. Le résultat doit être mesuré quand c'est possible (chiffre, test qui passe), pas seulement décrit.

## Registre

| ID | Date | Auteur | Module / tâche | Type | Modification | Pourquoi | Résultat mesuré | Statut | Détail |
|---|---|---|---|---|---|---|---|---|---|
| M01 | 01/10 | Gabriel | Tous | doc, outil | README, `requirements.txt`, `Makefile` (`make install`, `m1`, `m2-1`, `m2-2`) | Le dépôt n'avait ni documentation ni procédure d'installation | Le projet s'installe et se lance avec une commande par module | commité `fb3dd12` | — |
| M02 | 02/10 | Oscar | Module I | correction | Classement des dates 4D (`dados_semanticos.py`) | Les dates de fin étaient rangées dans « Início Real » ou perdues | IFC de test : 4 dates correctes sur 4 (avant : 1 sur 4) | commité `0c04fde` | [MODIFICATIONS.md §1](../MODIFICATIONS.md) |
| M03 | 02/10 | Oscar | Module I | amélioration | Nuage as-planned à densité uniforme, proportionnelle à la surface (`geometriaEnuvem.py`) | 2000 points par élément quelle que soit sa taille → densité très inégale | Le recalage passe de 0/4 à 4/4 réussites (analyse du 08/10, E8) | commité `0c04fde` | [MODIFICATIONS.md §3](../MODIFICATIONS.md) |
| M04 | 02/10 | Oscar | Module I | correction | Compatibilité IFC4X3 (`ifc_utils.py`) | `IfcBuildingElement` n'existe plus en IFC4X3 → plantage | Testé en IFC2X3 et IFC4X3 | commité `0c04fde` | [MODIFICATIONS.md §4](../MODIFICATIONS.md) |
| M05 | 02/10 | Oscar | Module I | correction | Dossiers de sortie créés, erreurs affichées (`dados_semanticos.py`, `geometriaEnuvem.py`) | Échecs silencieux | Erreurs visibles, sauvegardes vérifiées | commité `0c04fde` | [MODIFICATIONS.md §5](../MODIFICATIONS.md) |
| M06 | 02/10 | Oscar | Module II.1 | correction | Recentrage en float64 avant float32, PLY en double (`dataset_ponte.py`, `view_ia_result.py`, `txt_ply.py`) | Coordonnées UTM arrondies à 0,5 m | Grille de 5 cm : 20 valeurs distinctes conservées (avant : 3) | commité `bc758e3` | [MODIFICATIONS.md §2](../MODIFICATIONS.md) |
| M07 | 02/10 | Oscar | Module II.1 | correction | Dossier `test/` séparé de la validation (`dataset_ponte.py`) | Le test réutilisait la validation → scores optimistes | Avertissement affiché si `test/` est absent | commité `bc758e3` | [MODIFICATIONS.md §6](../MODIFICATIONS.md) |
| M08 | 02/10 | Oscar | Modules I et II.1 | correction | Chemins relatifs aux scripts au lieu de `/home/joserasj/...` | Le code ne tournait que sur une machine | Les scripts tournent depuis n'importe quel dossier | commité `0c04fde`, `bc758e3` | [MODIFICATIONS.md §7](../MODIFICATIONS.md) |
| M09 | 05/10 | Gabriel | Installation | correction | Open3D 0.20 + PyTorch 2.13, `open3d-cpu` sans GPU, contrôle de `libusb` | Versions d'Open3D et de PyTorch incompatibles | Installation vérifiée le 08/10 (CPU) : `import open3d.ml.torch` OK | commité `95baf78` | — |
| M10 | 05/10 | Gabriel | II.2 / T0.2 | nettoyage | Ancien script → `legacy/obbp_icp_v0.py`, suppression des `Zone.Identifier`, `outputs/` ignoré | Préparer la nouvelle architecture | Dossier propre, `make m2-2` pointe vers `legacy/` | commité `95baf78` | — |
| M11 | 06/10 | Gabriel | II.2 / architecture | structure | Paquet `registration/` (config, results, une fonction par étape), CLI `run_registration.py`, `inspect_clouds.py`, `benchmark_rotations.py` | Remplacer le script unique par un code modulaire et testable | `--help` OK ; chaque fonction indique sa tâche (`NotImplementedError("Tx.y")`) | commité `66fa2da` | — |
| M12 | 06/10 | Gabriel | II.2 / tests | test | `tests/` pytest avec ponts synthétiques (`conftest.py`) | Tester sans les vraies données | 15 tests collectés, tous en attente (`skip`) | commité `84168a3` | — |
| M13 | 08/10 | Oscar | II.2 | analyse, doc | Analyse initiale avec banc d'essai (12 expériences + RandLA-Net), documentation FR/EN du module, journal et suivi | Mesurer l'existant et vérifier le plan avant de coder | Voir le résumé ci-dessous | commité `0fd6293` | [analyse-initiale.fr.md](registration/analyse-initiale.fr.md) |
| M14 | 08/10 | Oscar | Tous | intégration | Récupération des commits de Gabriel et intégration de M02 à M08 : 4 conflits résolus (Makefile, README, requirements, .gitignore), choix d'Open3D de Gabriel conservé, modification de chemins de l'ancien script abandonnée ; WSL détecté automatiquement dans le Makefile | Les corrections du 02/10 n'étaient pas commitées et entraient en conflit avec le travail de Gabriel | Revérifié après intégration : compilation, 15 tests pytest, Module I (IFC4X3), dataset RandLA-Net, Makefile, banc d'essai identique | commité `0c04fde` à `0fd6293` (+ ce document) | [MODIFICATIONS.md](../MODIFICATIONS.md) |

## Résultats de référence (baseline)

Valeurs mesurées sur les ponts synthétiques de `tests/conftest.py`, avec l'ancien code inchangé (`legacy/obbp_icp_v0.py`), le 08/10. Elles servent de point de comparaison pour les tâches T1.x à T3.x. La baseline sur les vraies données D19 reste à faire (T0.1).

| Mesure | Ancien code (`make m2-2`) | Prototype des corrections prévues |
|---|---|---|
| Rotations réussies, pont asymétrique (8 angles) | 3/8 | 8/8 |
| Rotations réussies, pont presque symétrique | 4/8 | 8/8 |
| Pont construit à 70 %, 50 % ou 30 % | 0/12 | 0/12 (FPFH + RANSAC : 10/12) |
| Scan brut (terrain, grue, arbres) | 0/4 | 4/4 |
| BIM à 2000 points par élément | 0/4 (seuil 1 m) | 0/4 |
| Scan segmenté par RandLA-Net (22 % de points parasites restants) | 0/4 | 0/4 (FPFH + RANSAC après filtrage : 4/4) |
| Temps de calcul (50 000 points) | 0,6 s | 0,8 s (point-to-plane) à 1,7 s |

## Points en attente

- **Pousser les commits du 8 octobre** sur `origin/bridge-segmentation`, après accord d'Oscar.
- **Régénérer les nuages as-planned** (`make m1`) avec la densité uniforme, à partir des vrais modèles IFC.
- **Ajouter `logging.basicConfig(level=logging.INFO)` dans `train_ponte.py`** pour voir la perte et le mIoU pendant l'entraînement (analyse §5).

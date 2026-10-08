# Modifications : corrections et mise en route du dépôt

**Branche :** `bridge-segmentation` · **Date :** 2 octobre 2026 · **Base :** commit `fb3dd12` (README, requirements, Makefile de Gabriel)

> **Mise à jour du 8 octobre :** ces modifications ont été intégrées par-dessus les commits de Gabriel du 5 et du 6 octobre (`95baf78`, `66fa2da`, `84168a3`). Gabriel avait entre-temps réglé lui-même les points 8 et 10, avec une autre solution pour le point 8 : c'est la sienne qui est gardée. Les sections §7 à §11 sont à jour.

Ce document explique chaque modification de cette série : **où** elle se trouve, **pourquoi** elle a été faite, **comment** elle a été vérifiée, et **ce qu'elle change** pour vous. Les liens pointent vers les lignes concernées.

---

## Résumé

| # | Problème corrigé | Fichiers | Gravité |
|---|---|---|---|
| 1 | Les dates 4D extraites de l'IFC étaient mal rangées ou vides | `dados_semanticos.py` | 🔴 résultats faux |
| 2 | Perte de précision des coordonnées (≈ 0,5 m) avant l'entrée dans RandLA-Net | `dataset_ponte.py`, `view_ia_result.py`, `txt_ply.py` | 🔴 résultats faux |
| 3 | Densité de la nuage as-planned très inégale (2000 points par élément, quelle que soit sa taille) | `geometriaEnuvem.py` | 🟠 biais du recalage |
| 4 | Les scripts plantaient avec un IFC4X3 (le schéma des ponts) | `ifc_utils.py` (nouveau), `dados_semanticos.py`, `geometriaEnuvem.py` | 🟠 plantage |
| 5 | Échecs silencieux : dossiers absents, sauvegardes ratées, erreurs ignorées | `dados_semanticos.py`, `geometriaEnuvem.py` | 🟠 résultats manquants sans message |
| 6 | Le « test » du modèle tournait sur les données de validation | `dataset_ponte.py` | 🟠 scores trop optimistes |
| 7 | Chemins absolus vers la machine d'un autre utilisateur (`/home/joserasj/...`) | 6 scripts | 🟠 ne marche que sur une machine |
| 8 | Version d'Open3D incompatible avec la version de PyTorch installée | — (réglé par Gabriel, `95baf78`) | 🟠 installation cassée |
| 9 | Réglages WSL appliqués sur toutes les machines, aide du Makefile incomplète | `Makefile` | 🟡 confort |
| 10 | Fichiers parasites Windows commités | — (réglé par Gabriel, `95baf78`) | 🟡 propreté |

Le README a été mis à jour en conséquence (§11).

---

## 1. Dates 4D mal extraites — `dados_semanticos.py`

📍 [dados_semanticos.py:13-29](ModuleOne%20BIMtoPC/Python/dados_semanticos.py#L13-L29) (classification) et [L63-69](ModuleOne%20BIMtoPC/Python/dados_semanticos.py#L63-L69) (utilisation)

### Le problème

L'ancien code comparait le nom de la propriété **mis en minuscules** à des motifs qui contenaient **des majuscules** :

```python
chave_lower = chave.lower()
...
elif any(k in chave_lower for k in ['start', 'Contained in Task Start (Planned)', ...])
elif any(k in chave_lower for k in ['finish', 'Contained in Task Start (Actual)', ...])
```

`'Contained in Task Start (Actual)'` ne peut jamais être trouvé dans une chaîne en minuscules. Il ne restait donc que les motifs génériques, et les trois champs `Data_Inicio_Real`, `Data_Fim_Planejado` et `Data_Fim_Real` cherchaient tous le **même** mot (`'finish'`, `'fim'`, `'termino'`…). Résultat : la première date de fin trouvée était rangée dans *Início Real*, et les champs de fin restaient vides.

**Démonstration** sur un IFC de test avec les 4 propriétés classiques (`Contained in Task Start (Planned)` = 2026-01-10, `Start (Actual)` = 2026-01-15, `End (Planned)` = 2026-03-01, `End (Actual)` = 2026-03-20) :

| Champ | Attendu | Ancien code | Nouveau code |
|---|---|---|---|
| Data_Inicio_Planejado | 2026-01-10 | 2026-01-10 | 2026-01-10 |
| Data_Inicio_Real | 2026-01-15 | **2026-03-01** ❌ (c'est la fin prévue) | 2026-01-15 |
| Data_Fim_Planejado | 2026-03-01 | **vide** ❌ | 2026-03-01 |
| Data_Fim_Real | 2026-03-20 | **vide** ❌ | 2026-03-20 |

Ces dates alimentent l'étape IV de l'article (comparaison avec le planning). Avec l'ancien code, l'analyse d'avancement aurait été fausse.

### La correction

La propriété est classée en deux temps, avec des expressions régulières en minuscules :
1. **Événement** : début (`start`, `início`/`inicio`) ou fin (`finish`, `término`/`termino`, `end`, `fim`). `end` et `fim` doivent être des mots entiers (`\b`), pour ne pas capturer `extended`, `legend`, etc.
2. **Type** : réel si le nom contient `actual` ou `real`, prévu sinon.

```python
RE_INICIO = re.compile(r"start|in[ií]cio")
RE_FIM = re.compile(r"finish|t[eé]rmino|\bend\b|\bfim\b")
RE_REAL = re.compile(r"\bactual\b|\breal\b")
```

Deux garde-fous :
- **Seules les valeurs texte sont acceptées comme dates.** Sans ça, une propriété numérique comme `End Offset = 0.5` aurait été prise pour une date de fin (vérifié dans le test).
- **Le mot `schedule` a été retiré** des motifs : il était trop générique et capturait n'importe quelle propriété liée au planning.

Le reste ne change pas : volume, surface et coût sont cherchés comme avant, et la première valeur trouvée est conservée. `preço` (avec cédille) a été ajouté aux motifs de coût.

---

## 2. Perte de précision des coordonnées — `dataset_ponte.py`, `view_ia_result.py`, `txt_ply.py`

📍 [dataset_ponte.py:19-47](ModuleTwo%20RandlaNET/Python/dataset_ponte.py#L19-L47) (`carregar_ply`), [view_ia_result.py:30-31](ModuleTwo%20RandlaNET/Python/view_ia_result.py#L30-L31), [txt_ply.py:23-26](ModuleTwo%20RandlaNET/Python/txt_ply.py#L23-L26)

### Le problème

```python
points = np.vstack([...]).T.astype(np.float32)   # 1. conversion en float32
points = points - np.min(points, axis=0)          # 2. puis recentrage
```

Un `float32` n'a qu'environ 7 chiffres significatifs. Pour une coordonnée UTM comme 7 480 000 m (nord au Brésil), l'écart entre deux valeurs représentables est de **0,5 m**. En convertissant *avant* de recentrer, on arrondit chaque point à 50 cm près, et le recentrage arrive trop tard.

**Démonstration** sur une grille de points espacés de 5 cm, placée en coordonnées UTM :

| | Valeurs distinctes de y (attendu : 20) |
|---|---|
| Ancien code | **3** (0 ; 0,5 ; 1,0 m) — la grille est écrasée |
| Nouveau code | 20, erreur max 2·10⁻⁸ m |

### La correction

- On recentre **en float64**, puis on convertit en float32. Après recentrage, les valeurs sont petites et le float32 est assez précis.
- Ce code de lecture était dupliqué dans `dataset_ponte.py` et `view_ia_result.py`. Il est maintenant dans **une seule fonction**, `carregar_ply()`, utilisée par les deux scripts. Le modèle reçoit ainsi exactement les mêmes données à l'entraînement et à l'inférence.
- `txt_ply.py` déclarait `property float x/y/z` dans l'en-tête PLY. Le fichier lui-même stockait alors les coordonnées en float32, et la précision était perdue avant même la lecture. Elles sont maintenant déclarées en `double`. Chaîne testée de bout en bout : TXT en UTM → `txt_ply.py` → `carregar_ply()`, et les 20 valeurs sont conservées.

### ⚠️ Ce que ça change pour vous

- **Si vos nuages d'entraînement étaient en coordonnées géoréférencées (UTM)**, le modèle actuel (`ckpt_00050.pth`) a été entraîné sur des données dégradées. **Il faut le ré-entraîner** pour profiter de la correction.
- **Si elles étaient en coordonnées locales** (proches de 0, par exemple après un export CloudCompare recentré), rien ne change.
- Les PLY déjà générés par l'ancien `txt_ply.py` gardent leur précision dégradée. **Il faut les régénérer** à partir des TXT.

---

## 3. Densité de la nuage as-planned — `geometriaEnuvem.py`

📍 [geometriaEnuvem.py:13-20](ModuleOne%20BIMtoPC/Python/geometriaEnuvem.py#L13-L20) (paramètres) et [L67-73](ModuleOne%20BIMtoPC/Python/geometriaEnuvem.py#L67-L73) (calcul)

### Le problème

Chaque élément recevait **2000 points**, quelle que soit sa taille. Une travée de tablier de 50 m et un appareil d'appui de 50 cm avaient donc le même nombre de points : le tablier était très clairsemé et les petits éléments sur-représentés. Or l'ICP (module de recalage) et la mesure de couverture (étape III de l'article) supposent une densité à peu près uniforme. Une densité inégale biaise l'alignement vers les petits éléments.

### La correction

Le nombre de points est maintenant **proportionnel à la surface** de l'élément :

```python
n_pontos = max(pontos_minimos, int(mesh.get_surface_area() * densidade_pontos_m2))
```

- `densidade_pontos_m2 = 50` par défaut, soit un point tous les 14 cm environ. C'est largement assez pour le recalage, qui sous-échantillonne de toute façon à 20 cm (`voxel_size=0.2`).
- `pontos_minimos = 100` garantit que les petits éléments restent visibles.
- Les deux valeurs sont des paramètres de la fonction, à ajuster selon vos besoins.

**Vérifié :** sur le modèle de test, un mur de 50 m × 2 m reçoit 12 600 points et un mur de 2 m × 8 m en reçoit 2 100, proportionnellement à leur surface.

### ⚠️ Ce que ça change pour vous

- Le nombre total de points de la nuage as-planned change : il augmente pour les grands ouvrages. Le calcul peut être plus long sur un très gros modèle, car l'échantillonnage Poisson-disk est coûteux. Si c'est trop lent, baissez `densidade_pontos_m2`.
- Les nuages de `ModuleTwo Registration/AsPlanned/` ont été générées avec l'ancien code. Il faut les **régénérer** pour en profiter.

---

## 4. Compatibilité IFC4X3 — `ifc_utils.py` (nouveau)

📍 [ifc_utils.py](ModuleOne%20BIMtoPC/Python/ifc_utils.py), utilisé dans [dados_semanticos.py:39](ModuleOne%20BIMtoPC/Python/dados_semanticos.py#L39) et [geometriaEnuvem.py:25](ModuleOne%20BIMtoPC/Python/geometriaEnuvem.py#L25)

### Le problème

L'entité `IfcBuildingElement` a été **renommée `IfcBuiltElement` en IFC4X3**. C'est justement la version de l'IFC qui ajoute les ponts (`IfcBridge`, `IfcBearing`…). Avec un IFC4X3, l'ancien code plantait dès le départ :

```
RuntimeError: Entity with name 'IfcBuildingElement' not found in schema 'IFC4X3_ADD2'
```

Le fichier `comments.md` du module notait déjà « Testar com IFC recentes ».

### La correction

Une petite fonction `elementos_construidos(model)`, placée dans un fichier commun aux deux scripts, choisit la bonne entité selon le schéma du fichier. Elle sélectionne exactement les mêmes éléments qu'avant en IFC2X3 et IFC4.

**Vérifié** avec ifcopenshell 0.9 sur des IFC de test en IFC2X3 et en IFC4X3 : les deux scripts du module 1 tournent et donnent les mêmes résultats.

---

## 5. Échecs silencieux — `dados_semanticos.py`, `geometriaEnuvem.py`

📍 [dados_semanticos.py:95-97](ModuleOne%20BIMtoPC/Python/dados_semanticos.py#L95-L97), [geometriaEnuvem.py:41-46](ModuleOne%20BIMtoPC/Python/geometriaEnuvem.py#L41-L46), [L81-97](ModuleOne%20BIMtoPC/Python/geometriaEnuvem.py#L81-L97), [L99-105](ModuleOne%20BIMtoPC/Python/geometriaEnuvem.py#L99-L105)

### Les problèmes

- `dados_semanticos.py` écrivait dans `resultados_dados_semanticos/` sans créer ce dossier : `FileNotFoundError` à la première exécution.
- `geometriaEnuvem.py` créait `resultados_geometricos/` mais pas `resultado_nuvem_global/`. Or `o3d.io.write_point_cloud` ne lève **pas** d'erreur quand il échoue : il renvoie `False`. Le script affichait donc « Nuvem global salva em… » alors que rien n'était écrit.
- `except Exception: pass` cachait toutes les erreurs de géométrie : impossible de savoir quels éléments manquaient dans la nuage, ni pourquoi.

Le Makefile de Gabriel contournait les deux premiers points avec un `mkdir -p`, mais seulement pour `make m1`, pas si on lançait les scripts directement.

### La correction

- Les scripts créent eux-mêmes leurs dossiers de sortie. Le `mkdir -p` du Makefile n'est plus nécessaire et a été retiré.
- Le retour de `write_point_cloud` est vérifié, et une erreur claire est levée en cas d'échec.
- Les éléments **sans représentation géométrique** sont comptés à part (c'est normal, pas une erreur).
- Les **vraies erreurs** sont collectées et affichées en fin de traitement, avec le GlobalId, le type IFC et le message :

```
Processamento concluído. 2 de 3 elementos extraídos e convertidos.
1 elementos sem representação geométrica foram ignorados.
```

---

## 6. Le test tournait sur les données de validation — `dataset_ponte.py`

📍 [dataset_ponte.py:78-87](ModuleTwo%20RandlaNET/Python/dataset_ponte.py#L78-L87) et [L102-113](ModuleTwo%20RandlaNET/Python/dataset_ponte.py#L102-L113)

### Le problème

```python
elif split in ["test", "val", "validation"]:
    return self.val_files
```

`run_test()` (dans `test_ponte.py`) évaluait le modèle sur les **mêmes fichiers que la validation**, déjà utilisée pendant l'entraînement. Les scores obtenus ne mesurent pas la capacité du modèle sur une nuage qu'il n'a jamais vue : ils sont optimistes.

### La correction

- Le dataset lit maintenant un dossier `Ponte_Custom3D/test/`, en plus de `train/` et `val/`.
- **S'il n'existe pas, le comportement d'avant est conservé** (le test utilise la validation), mais un avertissement explicite s'affiche :
  ```
  AVISO: nenhum arquivo em .../test/. O teste vai usar os arquivos de validação e as métricas serão otimistas.
  ```
  Rien ne casse si vous n'avez pas encore de jeu de test.

👉 **À faire de votre côté :** mettre dans `test/` au moins une nuage annotée qui n'est ni dans `train/` ni dans `val/`, idéalement d'un autre pont ou d'une autre campagne de scan.

### Autres corrections dans ce fichier

- `num_points` renvoyait le **nombre de fichiers** au lieu du nombre de points. Il lit maintenant le nombre de points dans l'en-tête du PLY (`contar_pontos_ply`), sans charger la nuage ([L50-59](ModuleTwo%20RandlaNET/Python/dataset_ponte.py#L50-L59)).
- Le nom du fichier est extrait avec `os.path` au lieu de `split("/")`, ce qui marche aussi sous Windows.
- Si un fichier n'a pas de champ `label`, l'erreur dit clairement lequel.
- **Non modifié volontairement :** le « TRUQUE » `len(self.files) * 100` (chaque époque fait 100 passes sur les fichiers). Le changer modifierait la dynamique d'entraînement : c'est à décider ensemble (voir « Prochaines étapes »).

---

## 7. Chemins absolus — 6 scripts

📍 [dataset_ponte.py:11-16](ModuleTwo%20RandlaNET/Python/dataset_ponte.py#L11-L16), `train_ponte.py`, `test_ponte.py`, `view_ia_result.py`, `txt_ply.py`, `view_ground_truth.py`, `dados_semanticos.py`, `geometriaEnuvem.py`

### Le problème

Les scripts pointaient vers `/home/joserasj/RandlaNET/...` ou `/home/joserasj/Módulos/...` (deux variantes différentes !). Ils ne fonctionnaient sur aucune autre machine, et le README de Gabriel indiquait des emplacements que le code n'utilisait pas. D'autres scripts utilisaient des chemins relatifs au **dossier courant** (`../Modelos`, `./logs_ponte`) et ne marchaient que lancés depuis leur propre dossier.

### La correction

Tous les chemins sont maintenant calculés à partir de **l'emplacement du script** (`Path(__file__)`). Les scripts marchent depuis n'importe quel dossier et sur n'importe quelle machine, avec les emplacements décrits dans le README :

| Constante | Emplacement |
|---|---|
| `PASTA_DATASET` | `ModuleTwo RandlaNET/DATASET/` |
| `PASTA_PONTE_CUSTOM3D` | `ModuleTwo RandlaNET/DATASET/Ponte_Custom3D/` |
| `PASTA_LOGS` | `ModuleTwo RandlaNET/Python/logs_ponte/` |
| `CHECKPOINT_FINAL` | `.../logs_ponte/RandLANet_PonteDataset_torch/checkpoint/ckpt_00050.pth` |

Les chemins du module RandLA-Net sont définis **une seule fois**, dans `dataset_ponte.py`, et importés par `train_ponte.py`, `test_ponte.py` et `view_ia_result.py`. Pour changer de dossier, il n'y a qu'un endroit à modifier.

👉 **À faire de votre côté :** déplacer vos données (actuellement dans `/home/joserasj/...`) vers ces emplacements.

---

## 8. Version d'Open3D — réglé par Gabriel

### Le problème

Open3D-ML ne fonctionne qu'avec **la version exacte de PyTorch** pour laquelle il a été compilé. Le Makefile du 1er octobre installait PyTorch **2.2.2**, mais `open3d>=0.18` installait Open3D **0.20.0**, compilé pour PyTorch **2.13**. Résultat : `import open3d.ml.torch` échouait à la fin de `make install`.

Versions vérifiées en lisant la configuration de compilation des paquets officiels :

| Open3D | PyTorch attendu |
|---|---|
| 0.18.0 | 2.0.1 (CUDA 11.7) |
| 0.19.0 | 2.2.2 (CUDA 12.1) |
| **0.20.0** | **2.13.0 (CUDA 12.6)** |

### La solution retenue

Le 2 octobre, j'avais figé `open3d==0.19.0` pour rester sur PyTorch 2.2.2. Le 5 octobre, Gabriel a fait le choix inverse dans `95baf78` : **Open3D 0.20.0 + PyTorch 2.13**, installés par le Makefile (`open3d` avec GPU, `open3d-cpu` sinon), avec un contrôle de `libusb`. **C'est sa solution qui est gardée** : elle utilise les versions les plus récentes.

**Vérifié le 8 octobre (CPU) :** l'installation fonctionne et `import open3d.ml.torch` passe. Avec Open3D 0.20, seule la bibliothèque système `libusb-1.0-0` est nécessaire ; `libgomp1`, que demandait Open3D 0.19, ne l'est plus.

---

## 9. Makefile

📍 [Makefile:16-22](Makefile#L16-L22), [L30](Makefile#L30)

- Les trois variables d'affichage (`XDG_SESSION_TYPE`, `GDK_BACKEND`, `LIBGL_ALWAYS_SOFTWARE`) n'étaient utiles que sous WSL, mais elles étaient appliquées à **toutes** les commandes, sur toutes les machines. `LIBGL_ALWAYS_SOFTWARE=1` force un rendu 3D logiciel, très lent sur une machine Linux avec carte graphique. Elles ne s'appliquent maintenant **que sous WSL, détecté automatiquement**. On peut forcer le choix avec `make m2-2 WSL=1` ou `WSL=0`.
- `install` n'apparaissait pas dans `make help` : il lui manquait le commentaire `##`.
- Le `mkdir -p` de `m1` a été retiré, car les scripts créent maintenant leurs dossiers eux-mêmes (§5).

**Vérifié :** `make help` liste les 4 commandes, la détection WSL fonctionne (1 sous WSL, forçage à 0 ou 1 possible), et `make -n m1` produit la bonne commande.

---

## 10. Fichiers parasites — `*Zone.Identifier` — réglé par Gabriel

Deux fichiers vides, `asplanned_pointcloud_d19.ply:Zone.Identifier` et `asplanned_pointcloud_s07.ply:Zone.Identifier`, avaient été commités. Ce sont des métadonnées que Windows ajoute aux fichiers téléchargés ; elles apparaissent quand on copie ces fichiers vers WSL. Gabriel les a supprimés et a ajouté `*Zone.Identifier` au `.gitignore` dans `95baf78` (tâche T0.2).

---

## 11. README

- **Prérequis :** ajout de `make` à la commande `apt install` (il n'était pas installé sur le poste de test). `libusb-1.0-0` y était déjà, ajouté par Gabriel.
- **Données :** IFC2x3, IFC4 **ou IFC4X3** acceptés. Ajout du dossier `test/` et de son rôle. Les chemins sont relatifs aux modules.
- **Utilisation :** explication de la détection WSL et de l'option `WSL=0/1`.

---

## Ce qui n'a pas été modifié, et pourquoi

- **`visualizeIFC.py`** : l'analyse initiale supposait que `settings.USE_WORLD_COORDS` avait disparu dans ifcopenshell 0.8+. **C'était faux** : vérifié avec ifcopenshell 0.9, l'attribut existe toujours. Le fichier n'a pas été touché.
- **L'algorithme OBBP-ICP** (`legacy/obbp_icp_v0.py`) : rien n'a changé. La modification des chemins faite le 2 octobre a été abandonnée à l'intégration : après le déplacement du script dans `legacy/` par Gabriel, elle aurait pointé vers le mauvais dossier. Ses problèmes (seuil ICP de 20 m qui rend le choix du meilleur candidat peu fiable, étape `R_z` non implémentée, axes OBB tronqués en 2D) touchent la méthode elle-même. Les corriger demande des tests sur les vraies nuages, qui ne sont pas dans le dépôt.
- **Les classes `floor`/`column`** : d'après le README, RandLA-Net sert dans l'article à séparer le pont du reste (terrain, végétation, engins). Le choix des classes est à discuter avant d'y toucher.
- **`comandos.txt`** : conservé. Les variables qu'il contient sont désormais appliquées par le Makefile sous WSL, mais sa note sur `wsl --shutdown` reste utile.

## Ce qui n'a pas pu être testé

Les données (IFC du projet, nuages, dataset annoté, checkpoint) ne sont pas dans le dépôt, et la machine de test n'a pas de GPU. Voici ce qui a été vérifié et ce qui reste à faire :

| Vérifié | À vérifier par vous |
|---|---|
| Tous les fichiers Python compilent ; installation CPU (Open3D 0.20 + PyTorch 2.13) vérifiée le 8 octobre, après intégration | `make install` avec GPU |
| Module 1 sur des IFC de test IFC2X3 et IFC4X3 (dates, densité, dossiers, erreurs) | `make m1` sur le vrai modèle `RSP-116RJ-...ifc` |
| Lecture des PLY et précision sur des nuages UTM de test | `make m2-1` (entraînement + test) sur le vrai dataset |
| `txt_ply.py` → `carregar_ply()` de bout en bout | `view_ia_result.py` avec le checkpoint |
| Makefile : `help`, `-n m1`, détection WSL | `make m2-2` sur les vraies nuages |

## Prochaines étapes proposées

1. **Régénérer les données** : PLY via `txt_ply.py`, nuages as-planned via `make m1`. Puis **ré-entraîner** RandLA-Net si les coordonnées étaient en UTM (§2).
2. **Créer un vrai jeu de test** dans `Ponte_Custom3D/test/` (§6).
3. **Fiabiliser OBBP-ICP** : ICP multi-échelle (seuils décroissants), point-à-plan (la nuage BIM a des normales), choix du candidat sur la RMSE, et implémenter ou supprimer `R_z`. Supprimer aussi l'ancienne fonction `obbp_icp`, qui n'est plus utilisée.
4. **Garder le GlobalId de chaque point** dans la nuage as-planned globale. C'est indispensable pour l'étape III (état de chaque élément).
5. **Décider du « TRUQUE » ×100** du dataset : le remplacer par un vrai réglage du nombre d'itérations par époque.
6. **Écrire les étapes III et IV de l'article** (reconnaissance de l'état de chaque élément, puis analyse de l'avancement et des coûts).

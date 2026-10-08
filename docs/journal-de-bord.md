# Journal de bord — Bridge-Progress

Suivi du travail réalisé jour par jour sur le projet (stage, équipe : Oscar et Gabriel).
Les entrées viennent de l'historique git et des sessions de travail. Le détail de chaque modification est dans [suivi-des-modifications.md](suivi-des-modifications.md).

**Comment le remplir :** une ligne par jour travaillé, la plus récente en bas. Indiquer qui a fait quoi, en une phrase courte, avec le commit ou le document produit quand il y en a un.

| Date | Qui | Travail réalisé | Résultat / trace |
|---|---|---|---|
| Mercredi 30 septembre | Équipe d'origine | Dépôt initial du code existant : Module I (IFC → données sémantiques et nuage as-planned), Module II.1 (RandLA-Net), Module II.2 (recalage OBBP-ICP). Début du projet. | commit `279c6c6` |
| Jeudi 1er octobre | Gabriel | Rédaction du README (objectif, article de référence Tang & Shi 2026, schéma du pipeline), création de `requirements.txt` et du `Makefile` (installation, lancement des modules). | commit `fb3dd12` |
| Jeudi 1er octobre | Oscar | Analyse complète du dépôt (sujet, architecture, revue du code de chaque script) et liste de 31 propositions d'amélioration classées par priorité. | analyse (avec Claude Code) |
| Vendredi 2 octobre | Oscar | Corrections des Modules I et II.1 : dates 4D mal extraites, perte de précision des coordonnées, densité du nuage as-planned, compatibilité IFC4X3, jeu de test séparé, chemins absolus. Tests sur des IFC et des nuages synthétiques. | [MODIFICATIONS.md](../MODIFICATIONS.md) — non commité |
| Lundi 5 octobre | Gabriel | Correction de l'installation (Open3D 0.20 + PyTorch 2.13, version CPU sans GPU, vérification de `libusb`) et nettoyage du dossier Registration (ancien script déplacé dans `legacy/`, fichiers Windows supprimés). | commit `95baf78` |
| Mardi 6 octobre | Gabriel | Architecture du Module II.2 : paquet `registration/` (une fonction par étape de l'Algorithme 1), point d'entrée `run_registration.py`, scripts `inspect_clouds.py` et `benchmark_rotations.py`. | commit `66fa2da` |
| Mardi 6 octobre | Gabriel | Fichiers de tests pytest avec des ponts synthétiques (symétrique et asymétrique), tests désactivés en attendant les tâches. | commit `84168a3` |
| *Mercredi 7 octobre (date à confirmer)* | Oscar et Gabriel | Plan des tâches du Module II.2 (T0.1 à T4.1), premier test du code actuel sur pont synthétique, répartition des tâches dans Jira. | plan des tâches, Jira |
| Jeudi 8 octobre | Oscar | Analyse initiale du Module II.2 avec banc d'essai : 12 expériences sur ponts synthétiques et test de RandLA-Net, vérification de l'installation et du squelette. Mise en place du journal de bord, du suivi des modifications et de la documentation FR/EN du module. | [analyse](registration/analyse-initiale.fr.md), [plan FR](registration/plan.fr.md) / [EN](registration/plan.en.md) (avec Claude Code) |
| Jeudi 8 octobre | Oscar | Configuration de l'identité git, récupération des commits de Gabriel et intégration des corrections du 2 octobre (4 conflits résolus), revérification du code intégré, commits locaux. Oscar prend toutes les tâches du Module II.2 pour l'instant. | commits `0c04fde` à `0fd6293` (avec Claude Code) |

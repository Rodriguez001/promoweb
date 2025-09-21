# Prompts de Développement PromoWeb

Guide complet de prompts pour développer PromoWeb avec la stack technique Next.js 14, FastAPI, PostgreSQL+PostGIS.

## 1. 🎨 Frontend (Next.js 14 + TypeScript)

### 1.1. Configuration du projet Next.js 14 avec Tailwind CSS
```
Guide-moi pour configurer un projet Next.js 14 avec React 18 et TypeScript utilisant Tailwind CSS, tailwindcss-animate, et tailwind-merge. Intègre next-themes pour le dark/light mode, lucide-react pour les icônes, et Radix UI pour les composants accessibles. Configure le SEO avec next/head et le rendu côté serveur pour un e-commerce optimisé.
```

### 1.2. Catalogue produit avec React Query et Zod
```
Développe une interface de catalogue produit avec Next.js 14, en utilisant @tanstack/react-query pour la gestion d'état et le cache, react-hook-form avec zod pour la validation des filtres. Intègre des filtres par catégorie, prix (en XAF), marque et ISBN/EAN. Structure les composants avec TypeScript et style avec Tailwind CSS + Radix UI.
```

### 1.3. Promotions et ventes flash avec framer-motion
```
Crée une fonctionnalité de promotions avec Next.js 14 affichant des prix barrés et pourcentages de remise. Utilise framer-motion pour les animations et créer un minuteur dynamique de vente flash. Implémente la logique avec @tanstack/react-query pour synchroniser les données en temps réel avec le backend FastAPI.
```

### 1.4. Recherche intelligente avec axios et TypeScript
```
Intègre une barre de recherche instantanée avec Next.js 14 et TypeScript, utilisant axios pour communiquer avec le backend FastAPI. Ajoute l'autocomplétion par titre, auteur, marque ou ISBN avec debouncing. Style l'interface avec Tailwind CSS et Radix UI, et gère l'état avec @tanstack/react-query.
```

### 1.5. Design responsive et PWA avec Next.js
```
Optimise un site e-commerce Next.js 14 avec Tailwind CSS pour mobile, tablette et desktop. Configure le PWA avec next-pwa, ajoute le support offline avec service workers. Utilise next-themes pour la persistance du thème et lucide-react pour les icônes adaptatifs. Intègre les composants Radix UI pour l'accessibilité.
```

### 1.6. Intégration cartes avec MapLibre GL
```
Intègre une carte interactive avec maplibre-gl et react-map-gl dans Next.js 14 pour afficher les zones de livraison et points de retrait. Utilise TypeScript pour typer les données géospatiales, et @tanstack/react-query pour charger les données de localisation depuis le backend FastAPI + PostGIS.
```

### 1.7. Authentification avec NextAuth
```
Configure next-auth dans Next.js 14 pour l'authentification utilisateur avec support des providers OAuth (Google, Facebook) et authentification par email/password. Intègre avec le backend FastAPI utilisant python-jose pour la validation JWT. Style les pages de connexion avec Tailwind CSS et Radix UI.
```

## 2. ⚙️ Backend (FastAPI + PostgreSQL)

### 2.1. Configuration FastAPI avec SQLAlchemy et Alembic
```
Crée une API REST avec FastAPI, SQLAlchemy ORM et Alembic pour les migrations. Configure PostgreSQL avec PostGIS pour les données géospatiales. Utilise pydantic v2 pour la validation, python-jose pour JWT et passlib[bcrypt] pour le hashing. Structure les endpoints CRUD pour les produits, commandes et utilisateurs avec uvicorn/gunicorn.
```

### 2.2. Système de paiement partiel avec Pydantic
```
Développe un système de paiement partiel avec FastAPI et pydantic v2 pour valider les données. Calcule automatiquement un acompte de 30%, enregistre le solde dans PostgreSQL via SQLAlchemy. Intègre httpx pour communiquer avec les APIs de paiement (Orange Money, MTN, Stripe). Utilise alembic pour les migrations de schéma.
```

### 2.3. Synchronisation XML avec PostgreSQL et GeoAlchemy2
```
Implémente un système FastAPI pour synchroniser automatiquement les produits via XML Google Merchant. Utilise httpx pour récupérer les flux, SQLAlchemy + geoalchemy2 pour stocker les données géospatiales dans PostgreSQL+PostGIS. Ajoute pydantic-settings pour la configuration et planifie les tâches avec celery.
```

### 2.4. Calcul livraison avec shapely et PostGIS
```
Développe une API FastAPI pour calculer automatiquement les frais de livraison basés sur le poids/volume (stocké en PostgreSQL) et la géolocalisation (PostGIS + geoalchemy2 + shapely). Intègre Aftership/Sendcloud avec httpx pour le suivi en temps réel. Valide les données avec pydantic v2.
```

### 2.5. Notifications avec email-validator et httpx
```
Crée un système de notifications FastAPI utilisant email-validator pour valider les emails et httpx pour intégrer Twilio/Africastalking (SMS). Envoie des notifications automatiques (confirmation commande, rappel paiement, livraison). Stocke les templates en PostgreSQL et utilise python-multipart pour les uploads.
```

### 2.6. API de recherche avec PostgreSQL Full-Text Search
```
Implémente une API de recherche FastAPI utilisant PostgreSQL Full-Text Search pour rechercher dans le catalogue produit. Utilise SQLAlchemy pour les requêtes complexes, pydantic v2 pour structurer les réponses, et intègre la recherche par titre, description, marque, ISBN/EAN avec ranking et highlighting.
```

### 2.7. Cache et optimisation avec Redis
```
Intègre Redis comme cache pour FastAPI afin d'optimiser les performances des requêtes fréquentes (catalogue, prix, taux de change). Utilise aioredis pour les opérations asynchrones, configure la stratégie de cache avec TTL appropriés, et implémente la synchronisation entre PostgreSQL et Redis.
```

## 3. 💳 Système de Paiement (Stripe + Mobile Money)

### 3.1. Intégration multimodale avec FastAPI
```
Intègre les APIs Orange Money, MTN Mobile Money et Stripe dans FastAPI. Utilise httpx pour les appels API, pydantic v2 pour valider les réponses, et SQLAlchemy pour stocker les transactions en PostgreSQL. Gère les paiements partiels et remboursements avec python-jose pour la sécurité JWT.
```

### 3.2. Génération de reçus PDF avec FastAPI
```
Implémente un système FastAPI qui divise automatiquement les montants (acompte/solde) avec pydantic v2. Génère des reçus PDF avec ReportLab, stocke-les via python-multipart, et envoie par email avec email-validator. Utilise SQLAlchemy pour tracking des paiements en PostgreSQL.
```

### 3.3. Webhook de paiement sécurisés
```
Configure des webhooks sécurisés FastAPI pour recevoir les notifications de paiement de Stripe et Mobile Money. Utilise python-jose pour valider les signatures, pydantic v2 pour parser les données, et SQLAlchemy pour mettre à jour les statuts de commande en temps réel dans PostgreSQL.
```

### 3.4. Gestion des échecs et retry
```
Implémente un système de gestion des échecs de paiement avec FastAPI et Celery pour les retry automatiques. Stocke les tentatives en PostgreSQL via SQLAlchemy, utilise httpx avec exponential backoff pour les appels API, et notifie les utilisateurs via email-validator et SMS.
```

## 4. 🔄 Automatisation et Intégrations

### 4.1. Conversion EUR→XAF avec httpx et FastAPI
```
Intègre ExchangeRate API avec FastAPI utilisant httpx pour convertir EUR→XAF en temps réel. Utilise pydantic-settings pour la configuration API, SQLAlchemy pour cacher les taux en PostgreSQL. Implémente l'arrondi au multiple de 100 XAF avec des endpoints FastAPI validés par pydantic v2.
```

### 4.2. Import automatisé avec Alembic et PostgreSQL
```
Automatise l'import quotidien XML/CSV avec FastAPI, httpx pour récupérer les fichiers, et SQLAlchemy pour l'insertion en PostgreSQL. Utilise alembic pour les migrations de schéma, pydantic v2 pour valider les données, et python-multipart pour les uploads de fichiers.
```

### 4.3. Calcul prix final avec PostgreSQL et Pydantic
```
Crée un service FastAPI calculant les prix finaux (coût EUR + frais + taxes + marge) avec pydantic v2 pour la validation. Stocke les configurations en PostgreSQL via SQLAlchemy, utilise geoalchemy2 pour les taxes par région. Expose des endpoints REST pour le frontend Next.js.
```

### 4.4. Tâches planifiées avec Celery
```
Configure Celery avec FastAPI pour les tâches en arrière-plan : synchronisation produits, calcul prix, envoi notifications, nettoyage cache. Utilise Redis comme broker, SQLAlchemy pour logger les tâches, et pydantic v2 pour valider les paramètres des tâches.
```

### 4.5. Monitoring et logging
```
Implémente un système de monitoring FastAPI avec Sentry pour le tracking d'erreurs, Prometheus/Grafana pour les métriques, et structlog pour les logs structurés. Intègre avec PostgreSQL pour stocker les métriques business et utilise pydantic v2 pour formater les logs.
```

## 5. 📊 Gestion des Commandes et Dashboard

### 5.1. Dashboard admin avec Next.js et FastAPI
```
Développe un dashboard admin avec Next.js 14, @tanstack/react-query pour les données temps réel, et Radix UI pour l'interface. Connecte à des endpoints FastAPI (SQLAlchemy + PostgreSQL) pour afficher statuts commandes, KPIs ventes, et délais livraison. Utilise next-auth pour l'authentification admin.
```

### 5.2. Système de remboursement avec PostgreSQL
```
Implémente une fonctionnalité de remboursement FastAPI avec SQLAlchemy pour tracking en PostgreSQL. Utilise pydantic v2 pour valider les montants, httpx pour communiquer avec les APIs de paiement (remboursements Stripe/Mobile Money). Intègre des endpoints sécurisés avec python-jose (JWT).
```

### 5.3. Gestion des stocks en temps réel
```
Crée un système de gestion des stocks FastAPI avec PostgreSQL pour tracking en temps réel. Utilise SQLAlchemy pour les transactions atomiques, WebSockets pour notifier le frontend Next.js des changements de stock, et pydantic v2 pour valider les mouvements de stock.
```

### 5.4. Workflow de commandes avec état
```
Implémente une machine à états pour les commandes avec FastAPI et SQLAlchemy. Définis les transitions (en attente → payé partiellement → expédié → livré) avec pydantic v2 pour valider les changements d'état. Intègre les notifications automatiques via email-validator.
```

### 5.5. Rapports et exports avec FastAPI
```
Développe des endpoints FastAPI pour générer des rapports de ventes (PDF/Excel) avec SQLAlchemy pour les requêtes complexes PostgreSQL. Utilise pandas pour l'analyse de données, openpyxl pour Excel, et ReportLab pour PDF. Structure les données avec pydantic v2.
```

## 6. 📈 Analytics et Business Intelligence

### 6.1. Analytics avec Next.js et PostgreSQL
```
Intègre Google Analytics 4 dans Next.js 14 avec des événements personnalisés (recherche, ajout panier, conversion). Stocke les métriques business en PostgreSQL via FastAPI + SQLAlchemy. Crée un dashboard avec @tanstack/react-query et Radix UI pour visualiser les données analytiques.
```

### 6.2. Calcul marges avec PostGIS et SQLAlchemy
```
Développe des endpoints FastAPI pour calculer marges par produit/catégorie et chiffre d'affaires par géolocalisation (Douala, Yaoundé) en utilisant PostGIS + geoalchemy2 + shapely. Utilise SQLAlchemy pour les requêtes complexes PostgreSQL et pydantic v2 pour structurer les réponses JSON.
```

### 6.3. Segmentation client avec Machine Learning
```
Implémente un système de segmentation client avec FastAPI et scikit-learn. Analyse les données de commandes stockées en PostgreSQL via SQLAlchemy, crée des clusters clients, et utilise pydantic v2 pour structurer les profils. Intègre les recommandations dans le frontend Next.js.
```

### 6.4. A/B Testing avec Analytics
```
Configure un système d'A/B testing avec Next.js 14 pour tester différentes versions du frontend. Stocke les résultats en PostgreSQL via FastAPI + SQLAlchemy, utilise pydantic v2 pour valider les événements, et analyse les performances avec des requêtes SQL optimisées.
```

### 6.5. Prédiction de demande avec TimeSeries
```
Développe un modèle de prédiction de demande avec FastAPI et Prophet/ARIMA. Utilise les données historiques PostgreSQL via SQLAlchemy, entraîne les modèles avec pandas/numpy, et expose les prédictions via des endpoints REST avec pydantic v2 pour la validation.
```

## 7. 🚀 Déploiement et Infrastructure

### 7.1. Hébergement avec Docker Compose
```
Configure le déploiement PromoWeb sur Cloudways avec Docker Compose. Utilise l'image postgis/postgis:15-3.4 pour PostgreSQL+PostGIS, pgAdmin pour l'administration DB. Déploie le frontend Next.js et backend FastAPI avec uvicorn/gunicorn. Configure SSL et CDN pour optimiser les performances.
```

### 7.2. CI/CD avec GitHub Actions
```
Configure un pipeline GitHub Actions pour déployer automatiquement Next.js 14 (frontend) et FastAPI (backend) avec Docker. Utilise pytest + pytest-asyncio + pytest-cov pour les tests backend, vitest + @testing-library/* + msw pour le frontend. Intègre black, isort, flake8, mypy pour la qualité code Python.
```

### 7.3. Monitoring et observabilité
```
Configure le monitoring production avec Prometheus, Grafana, et Loki pour les métriques et logs. Intègre Sentry pour le tracking d'erreurs FastAPI et Next.js. Utilise Docker healthchecks et configure les alertes pour PostgreSQL, Redis, et les services applicatifs.
```

### 7.4. Backup et disaster recovery
```
Implémente une stratégie de backup automatisée pour PostgreSQL avec pg_dump, stockage cloud S3, et restauration testée. Configure la réplication PostgreSQL pour la haute disponibilité, et documente les procédures de disaster recovery avec RTO/RPO définis.
```

### 7.5. Scaling et performance
```
Optimise les performances PromoWeb avec load balancing NGINX, cache Redis, et CDN Cloudflare. Configure le scaling horizontal FastAPI avec Kubernetes ou Docker Swarm, optimise les requêtes PostgreSQL avec indexation, et implémente la pagination avec cursor-based pagination.
```

## 8. 🧪 Tests et Qualité Code

### 8.1. Tests Frontend (Next.js)
```
Configure l'environnement de test pour Next.js 14 avec vitest, @testing-library/react, @testing-library/jest-dom, et msw pour mocker les APIs. Teste les composants Radix UI, la validation zod, et l'intégration @tanstack/react-query avec jsdom. Utilise eslint + prettier pour la qualité code.
```

### 8.2. Tests Backend (FastAPI)
```
Configure pytest + pytest-asyncio + pytest-cov pour tester les endpoints FastAPI. Mock les dépendances SQLAlchemy, teste la validation pydantic v2, et l'authentification python-jose. Utilise black + isort + flake8 + mypy pour maintenir la qualité code Python avec poetry.
```

### 8.3. Tests d'intégration avec PostgreSQL
```
Implémente des tests d'intégration FastAPI avec une base PostgreSQL de test. Utilise pytest-postgresql pour créer des instances temporaires, teste les migrations alembic, et valide les requêtes PostGIS avec geoalchemy2. Configure les fixtures pour les données de test.
```

### 8.4. Tests E2E avec Playwright
```
Configure des tests end-to-end avec Playwright pour Next.js 14. Teste les parcours utilisateur complets (catalogue, panier, paiement), mock les APIs de paiement, et valide l'interface responsive sur différents devices. Intègre dans le pipeline CI/CD GitHub Actions.
```

### 8.5. Performance testing avec Locust
```
Implémente des tests de charge avec Locust pour valider les performances FastAPI sous charge. Teste la scalabilité PostgreSQL, la performance des endpoints critiques, et mesure les temps de réponse. Configure le monitoring des ressources système pendant les tests.
```

## 9. 🔒 Sécurité et Conformité

### 9.1. Sécurisation FastAPI avec OAuth2
```
Implémente OAuth2 + JWT avec FastAPI et python-jose pour sécuriser les endpoints. Configure les scopes pour les différents rôles (utilisateur, admin), valide les tokens avec pydantic v2, et intègre avec PostgreSQL pour stocker les sessions. Ajoute rate limiting et CORS.
```

### 9.2. Chiffrement des données sensibles
```
Configure le chiffrement des données sensibles en PostgreSQL avec pgcrypto. Utilise passlib[bcrypt] pour les mots de passe, chiffre les informations de paiement avec AES-256, et implémente la rotation des clés. Assure la conformité RGPD pour les données personnelles.
```

### 9.3. Audit et logging sécurisé
```
Implémente un système d'audit FastAPI pour tracer toutes les actions sensibles (connexions, paiements, modifications admin). Stocke les logs en PostgreSQL avec horodatage, utilise structlog pour formater, et configure la rétention des logs selon la conformité RGPD.
```

### 9.4. Validation et sanitisation des données
```
Configure la validation stricte avec pydantic v2 pour tous les inputs FastAPI. Implémente la sanitisation contre XSS, SQL injection, et CSRF. Utilise SQLAlchemy avec parameterized queries, valide les uploads de fichiers avec python-multipart, et configure les headers de sécurité.
```

---

## 📝 Notes d'utilisation

Ces prompts sont conçus pour être utilisés avec des outils d'IA comme:
- **Claude/ChatGPT** pour la génération de code
- **GitHub Copilot** pour l'assistance au développement
- **Cursor/VSCode** avec extensions IA

### Structure des prompts
- ✅ **Technologies spécifiques** : utilise exactement la stack PromoWeb
- ✅ **Contexte métier** : adapté aux besoins e-commerce camerounais
- ✅ **Détails techniques** : inclut les librairies et outils spécifiques
- ✅ **Bonnes pratiques** : intègre les standards de qualité et sécurité

### Utilisation recommandée
1. **Copier le prompt** correspondant à votre besoin
2. **Adapter le contexte** si nécessaire (noms de fichiers, spécificités)
3. **Itérer** sur la réponse pour affiner le code généré
4. **Tester** le code dans votre environnement de développement

---

*Dernière mise à jour : Septembre 2024*
*Stack technique : Next.js 14, FastAPI, PostgreSQL+PostGIS, Docker*

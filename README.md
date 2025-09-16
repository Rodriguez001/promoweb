# PromoWeb Africa - E-commerce Platform

Plateforme e-commerce innovante spécialisée dans les produits européens de parapharmacie, beauté, bien-être, et livres à destination des consommateurs camerounais.

## 🚀 Technologies

### Frontend
- **Next.js 14** avec App Router
- **React 18** avec TypeScript
- **Tailwind CSS** pour le design moderne et responsive
- **PWA** pour une expérience native
- **Algolia Search** pour la recherche intelligente

### Backend
- **NestJS** avec TypeScript
- **PostgreSQL** pour la base de données
- **Prisma ORM** pour la gestion des données
- **Redis** pour le cache et les sessions

### Paiements
- **Mobile Money** (Orange Money, MTN Mobile Money)
- **Cartes bancaires** via RHOPEN Labs API
- **Système d'acompte** configurable

### Livraison
- **Suivi en temps réel** via APIs DHL/transporteurs
- **Calcul automatique** des frais selon poids/volume

## 🎯 Public Cible

- **Démographie**: Consommateurs urbains 25-45 ans, classe moyenne connectée
- **Localisation**: Douala, Yaoundé principalement
- **Intérêts**: Produits européens de qualité (beauté, bien-être, livres)

## 🏗️ Architecture

```
promoweb-africa/
├── frontend/          # Next.js application
├── backend/           # NestJS API
├── database/          # PostgreSQL schemas & migrations
├── docs/             # Documentation
└── docker/           # Docker configuration
```

## 🚦 Démarrage Rapide

```bash
# Installation des dépendances
npm run install:all

# Développement
npm run dev

# Production
npm run build
npm start
```

## 📋 Fonctionnalités Principales

### ✅ Catalogue Produit
- Affichage optimisé avec images HD
- Filtres avancés (marque, catégorie, prix, ISBN/EAN)
- Promotions et ventes flash
- Recherche intelligente

### ✅ Commandes & Paiement
- Calcul automatique acompte + solde
- Codes promo et réductions
- Paiement Mobile Money + CB
- Notifications automatisées

### ✅ Livraison
- Frais automatisés selon poids/volume
- Livraison domicile ou point relais
- Suivi temps réel des colis

### ✅ Administration
- Gestion stocks avec synchronisation automatique
- Interface commandes et paiements
- Tableau de bord KPI
- Conversion EUR → XAF en temps réel

## 🌍 Conformité

- ❌ Exclusion produits sur prescription
- ✅ Conformité RGPD
- ✅ Sécurité SSL/TLS
- ✅ Réglementations douanières locales

## 📱 Support

- **Bilingue**: Français/Anglais
- **Responsive**: Mobile, tablette, desktop
- **Accessibilité**: Conforme WCAG 2.1

---

*Développé pour simplifier l'accès aux produits européens de qualité au Cameroun*
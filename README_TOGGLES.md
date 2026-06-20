# À propos des toggles (switches) dans Home Assistant

## Problèmes connus avec l'interface

### 1. Toggle à côté du Color Picker
Le toggle (switch) qui apparaît à côté de l'entité "Color Picker" est un comportement **natif et obligatoire** de Home Assistant pour toutes les entités de type "Light" (lumière).

**Pourquoi ce toggle existe-t-il ?**
- Home Assistant traite tous les Color Pickers comme des lumières
- Toutes les lumières ont un bouton on/off dans l'interface
- Il n'est pas possible de désactiver ce toggle sans modifier complètement le type d'entité

**Solutions possibles :**

#### Option A: Accepter le toggle (recommandé)
Le toggle ne fait rien de mal - il reste toujours "ON" car un color picker est toujours actif.

#### Option B: Masquer le toggle avec card-mod (avancé)
Installez [card-mod](https://github.com/thomasloven/lovelace-card-mod) et utilisez cette configuration dans votre dashboard:

```yaml
type: entities
entities:
  - entity: light.esp_color_picker
card_mod:
  style:
    hui-generic-entity-row:
      $: |
        ha-switch {
          display: none !important;
        }
```

#### Option C: Créer une entité personnalisée (très avancé)
Modifier le code pour créer un type d'entité complètement différent qui ne dérive pas de LightEntity.

### 2. Switch en haut à côté du nom de l'appareil
Le switch qui apparaît en haut à côté du nom "esp" n'est **pas un switch supplémentaire**. C'est simplement Home Assistant qui affiche un "contrôle rapide" pour la première entité switch de votre appareil.

**Ce que vous voyez :**
- En haut: "esp" avec switch → C'est le contrôle rapide du premier switch
- Plus bas: "Switch" → C'est le même switch affiché normalement

**C'est le comportement normal de Home Assistant** pour permettre un accès rapide aux contrôles principaux de l'appareil.

**Solutions possibles :**

#### Option 1: Ignorer ce comportement (recommandé)
Ce n'est pas un bug, c'est une fonctionnalité de Home Assistant pour faciliter l'accès.

#### Option 2: Désactiver l'affichage de la carte d'appareil
Dans votre dashboard, au lieu d'afficher la carte de l'appareil, affichez directement les entités individuelles:

```yaml
type: entities
entities:
  - entity: switch.esp_switch
  - entity: switch.esp_switch2
  - entity: light.esp_color_picker
  - entity: sensor.esp_gauge
  # etc.
```

#### Option 3: Personnaliser complètement avec une carte Lovelace
Créez une carte personnalisée qui affiche exactement ce que vous voulez voir.

## Résumé

Les deux "problèmes" que vous observez sont en fait des **comportements normaux de Home Assistant** :

1. ✅ Le toggle du Color Picker existe parce que c'est une lumière
2. ✅ Le switch en haut est un contrôle rapide (c'est le même que "Switch")

**Aucun de ces éléments n'est un bug** - c'est simplement la façon dont Home Assistant fonctionne par défaut.

Si vous souhaitez une interface complètement personnalisée, vous devrez créer une carte Lovelace personnalisée ou utiliser des modules complémentaires comme card-mod.

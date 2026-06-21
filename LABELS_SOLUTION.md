# Problème des Labels sur les Boutons GyverHub

## Symptômes

Les boutons de votre intégration GyverHub dans Home Assistant affichent des noms génériques au lieu des labels que vous avez définis dans GyverHub Desktop :
- `ESP_n1`, `ESP_n2`, etc.
- `ceterra`

Ces labels apparaissent même sur votre version Desktop de GyverHub où tout fonctionne correctement.

## Cause Probable

Le problème vient du fait que les données JSON reçues de l'ESP ne contiennent pas les champs `label` ou `text` avec les noms que vous avez configurés. Cela peut se produire pour plusieurs raisons :

1. L'ESP envoie des noms par défaut qui ne sont pas les labels que vous avez configurés
2. Il y a un problème de synchronisation entre GyverHub Desktop et votre ESP
3. Les données JSON sont mal formatées ou incomplètes

## Solutions

### Solution 1 : Activer les logs DEBUG (Recommandé)

Ceci permettra de voir exactement quelles données sont reçues de votre ESP.

1. **Copiez le fichier** `DEBUG_LOGGER.yaml` dans votre dossier de configuration Home Assistant (`config/logger.yaml`)
2. **Redémarrez Home Assistant**
3. **Regardez les logs** pour trouver les lignes contenant `=== Button Details ===`

#### Exemple de logs attendus avec la correction :

```
=== Button Details ===
Button: id='btn_0', label='Mon Bouton', widget_type='button', icon='mdi:play'
Button: id='btn_1', label='Bouton 2', widget_type='button', icon='mdi:stop'
```

#### Avec le problème (sans correction) :

```
=== Button Details ===
Button: id='btn_0', label='', widget_type='button', icon='mdi:play'
```

### Solution 2 : Utiliser le label généré automatiquement

J'ai ajouté une correction automatique qui génère un label descriptif basé sur le type de widget :

- `button_0` → "Bouton 1"
- `switch_0` → "Switch 1"
- `led_0` → "LED 1"
- etc.

Cette solution permet d'avoir des noms descriptifs même si les labels ne sont pas transmis.

### Solution 3 : Configurer les labels dans l'ESP (Pour les développeurs)

Si vous connaissez le code de votre ESP, vous pouvez modifier les données JSON pour inclure les labels corrects :

```json
{
  "type": "button",
  "id": "btn_0",
  "label": "Mon Bouton",
  "icon": "mdi:play"
}
```

### Solution 4 : Utiliser le fichier de configuration personnalisée (À venir)

Je prévois d'ajouter une fonctionnalité pour configurer des labels personnalisés dans l'interface d'Home Assistant.

## Démarches pour résoudre le problème

1. **Testez avec les logs** - Activez les logs DEBUG pour voir les données reçues
2. **Vérifiez les données** - Comparez les données reçues avec celles de GyverHub Desktop
3. **Appliquez la correction** - Utilisez la correction automatique si les labels sont vides
4. **Contactez le support** - Si le problème persiste, ouvrez un ticket sur le repository

## Fichiers de correction

Les modifications ont été apportées dans ces fichiers :

1. `custom_components/gyverhub/button.py` - Ajout des logs pour les boutons
2. `custom_components/gyverhub/protocol.py` - Génération automatique de labels et logs détaillés
3. `custom_components/gyverhub/coordinator.py` - Logs détaillés pour tous les widgets

## Prochaines étapes

1. Redémarrez Home Assistant pour appliquer les modifications
2. Activez les logs DEBUG si nécessaire
3. Consultez les logs pour identifier le problème
4. Si les labels sont toujours vides, utilisez les labels générés automatiquement

## Support

Si vous rencontrez des problèmes avec cette intégration, ouvrez un ticket sur le repository GitHub avec :
- Les logs DEBUG (avec les données reçues)
- Une capture d'écran des boutons dans GyverHub Desktop
- Une capture d'écran des boutons dans Home Assistant
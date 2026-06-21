# Bug Labels Boutons GyverHub - Documentation

## Problème

Les boutons de l'intégration GyverHub dans Home Assistant affichent les IDs (ex: "ESP_n1", "ESP_n2", "ceterra") au lieu des labels corrects que l'utilisateur a configurés dans GyverHub Desktop.

## Analyse

### Code actuel

Dans tous les fichiers de widgets (`button.py`, `switch.py`, `light.py`, etc.) :

```python
self._attr_name = widget.label or widget.id
```

Le bouton utilise le champ `label` ou `widget.id` pour le nom de l'entité.

### Données JSON reçues

Les widgets sont créés depuis les données JSON de l'ESP via `BaseWidget.from_dict()` :

```python
@classmethod
def from_dict(cls, data: Dict) -> 'BaseWidget':
    return cls(
        id=data.get("id", data.get("name", "")),
        widget_type=data.get("type", ""),
        label=data.get("label", data.get("text", "")),
        ...
    )
```

### Hypothèse du problème

Il est possible que les données JSON reçues par MQTT ne contiennent pas les champs `label` ou `text` avec les valeurs correctes.

## Modifications apportées

### 1. `button.py`
- Ajout de logs pour afficher les détails des boutons lors de leur création

### 2. `protocol.py`
- Ajout de logs détaillés dans `from_dict()` pour afficher ce qui est reçu des données JSON
- Affichage des clés présentes dans les données du widget

### 3. `coordinator.py`
- Ajout de logs détaillés pour afficher tous les widgets après mise à jour de l'UI
- Affichage séparé des boutons, switchs, LEDs et autres widgets
- Affichage des champs `id`, `label`, `widget_type` et `icon` pour chaque widget

## Résolution

Pour résoudre ce problème, nous devons :

1. **Activer les logs DEBUG** pour voir ce qui est réellement reçu des boutons
2. **Vérifier les données JSON** reçues par MQTT pour voir la structure exacte
3. **Corriger le parsing** si les labels ne sont pas dans les champs attendus

## Commandes pour activer les logs

```bash
# Activer les logs DEBUG pour GyverHub
logger: default = debug
logger:
  gyverhub: debug
```

## Exemple de logs attendus

Après les modifications, les logs devraient afficher quelque chose comme :

```
=== Button Details ===
Button: id='btn_1', label='Mon Bouton', widget_type='button', icon='mdi:play'
Button: id='btn_2', label='Bouton 2', widget_type='button', icon='mdi:stop'
```

Si les labels sont vides, cela montrera :

```
=== Button Details ===
Button: id='btn_1', label='', widget_type='button', icon='mdi:play'
```

## Résolution potentielle

Si les données JSON ne contiennent pas les labels, il faudra :

1. Modifier la méthode `from_dict()` pour utiliser d'autres champs possibles
2. Ajouter un mappage des labels depuis un fichier de configuration
3. Demander aux utilisateurs de configurer les labels directement dans l'URL ou le code de l'ESP

## Suivi

- [x] Ajout des logs pour debug
- [ ] Analyse des logs pour identifier la cause
- [ ] Correction du parsing des labels
- [ ] Vérification avec les données réelles des ESP
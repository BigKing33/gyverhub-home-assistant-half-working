# About Toggles (Switches) in Home Assistant

## Known Interface Issues

### 1. Toggle Next to the Color Picker

The toggle (switch) that appears next to the "Color Picker" entity is a native and required behavior of Home Assistant for all entities of the "Light" type.

**Why does this toggle exist?**
- Home Assistant treats all Color Pickers as lights
- All lights have an on/off button in the interface
- It is not possible to disable this toggle without completely changing the entity type

**Possible solutions:**

**Option A: Accept the toggle (recommended)**
The toggle does no harm — it always stays "ON" because a color picker is always active.

**Option B: Hide the toggle using card-mod (advanced)**
Install card-mod and use this configuration in your dashboard:

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

**Option C: Create a custom entity (very advanced)**
Modify the code to create a completely different entity type that does not derive from LightEntity.

### 2. Switch at the Top Next to the Device Name

The switch shown at the top next to the name "esp" is not an additional switch. It is simply Home Assistant displaying a "quick control" for the first switch entity of your device.

**What you see:**
- Top: "esp" with a switch → quick control of the first switch
- Below: "Switch" → the same switch shown normally

This is normal Home Assistant behavior designed to provide quick access to the main device controls.

**Possible solutions:**

**Option 1: Ignore this behavior (recommended)**
This is not a bug, but a Home Assistant feature.

**Option 2: Disable the device card view**
Instead of showing the device card, display individual entities directly in your dashboard:

```yaml
type: entities
entities:
  - entity: switch.esp_switch
  - entity: switch.esp_switch2
  - entity: light.esp_color_picker
  - entity: sensor.esp_gauge
```

**Option 3: Fully customize with a Lovelace card**
Create a custom card that displays exactly what you want to see.

## Summary

The two "issues" you are observing are actually normal Home Assistant behavior:

- ✅ The Color Picker toggle exists because it is treated as a light
- ✅ The top switch is a quick control (it is the same as the "Switch" below)

None of these elements are bugs — this is simply how Home Assistant works by default.

If you want a fully customized interface, you will need to create a custom Lovelace card or use add-ons such as card-mod.

---

## 🇷🇺 Русский перевод

# О переключателях (switches) в Home Assistant

## Известные проблемы интерфейса

### 1. Переключатель рядом с Color Picker

Переключатель (toggle), который отображается рядом с сущностью "Color Picker", является нативным и обязательным поведением Home Assistant для всех сущностей типа "Light" (освещение).

**Почему существует этот переключатель?**
- Home Assistant рассматривает все Color Picker как источники света
- У всех источников света есть кнопка включения/выключения в интерфейсе
- Нельзя отключить этот переключатель без полного изменения типа сущности

**Возможные решения:**

**Вариант A: Оставить как есть (рекомендуется)**
Переключатель не приносит вреда — он всегда остаётся "ON", потому что Color Picker всегда активен.

**Вариант B: Скрыть переключатель через card-mod (продвинутый способ)**
Установите card-mod и используйте эту конфигурацию в вашем dashboard:

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

**Вариант C: Создать кастомную сущность (очень продвинутый способ)**
Изменить код так, чтобы создать полностью другой тип сущности, не наследующий LightEntity.

### 2. Переключатель сверху рядом с названием устройства

Переключатель, который отображается сверху рядом с названием "esp", не является дополнительным переключателем. Это просто Home Assistant показывает "быстрый доступ" к первой сущности типа switch устройства.

**Что вы видите:**
- Сверху: "esp" с переключателем → быстрый доступ к первому switch
- Ниже: "Switch" → тот же самый переключатель в обычном виде

Это нормальное поведение Home Assistant, предназначенное для быстрого доступа к основным элементам управления устройством.

**Возможные решения:**

**Вариант 1: Игнорировать (рекомендуется)**
Это не ошибка, а функция Home Assistant.

**Вариант 2: Отключить карточку устройства**
Вместо карточки устройства показывайте отдельные сущности:

```yaml
type: entities
entities:
  - entity: switch.esp_switch
  - entity: switch.esp_switch2
  - entity: light.esp_color_picker
  - entity: sensor.esp_gauge
```

**Вариант 3: Полная кастомизация через Lovelace**
Создать собственную карточку, которая отображает всё точно так, как нужно.

## Резюме

Обе "проблемы", которые вы наблюдаете, на самом деле являются нормальным поведением Home Assistant:

- ✅ Переключатель Color Picker существует, потому что это тип "light"
- ✅ Верхний переключатель — это быстрый доступ (тот же самый, что и ниже)

Никакого бага здесь нет — это стандартное поведение системы.

Если нужна полностью кастомная интерфейсная логика, необходимо использовать кастомные карточки Lovelace или расширения вроде card-mod.
# About Toggles (Switches) in Home Assistant

## Known Interface Issues

### 1. Toggle Next to the Color Picker

The toggle (switch) that appears next to the "Color Picker" entity is a native and required behavior of Home Assistant for all entities of the "Light" type.

**Why does this toggle exist?**
- Home Assistant treats all Color Pickers as lights
- All lights have an on/off button in the interface
- It is not possible to disable this toggle without completely changing the entity type

**Possible solutions:**

**Option A: Accept the toggle (recommended)**
The toggle does no harm — it always stays "ON" because a color picker is always active.

**Option B: Hide the toggle using card-mod (advanced)**
Install card-mod and use this configuration in your dashboard:

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

**Option C: Create a custom entity (very advanced)**
Modify the code to create a completely different entity type that does not derive from LightEntity.

### 2. Switch at the Top Next to the Device Name

The switch shown at the top next to the name "esp" is not an additional switch. It is simply Home Assistant displaying a "quick control" for the first switch entity of your device.

**What you see:**
- Top: "esp" with a switch → quick control of the first switch
- Below: "Switch" → the same switch shown normally

This is normal Home Assistant behavior designed to provide quick access to the main device controls.

**Possible solutions:**

**Option 1: Ignore this behavior (recommended)**
This is not a bug, but a Home Assistant feature.

**Option 2: Disable the device card view**
Instead of showing the device card, display individual entities directly in your dashboard:

```yaml
type: entities
entities:
  - entity: switch.esp_switch
  - entity: switch.esp_switch2
  - entity: light.esp_color_picker
  - entity: sensor.esp_gauge
```

**Option 3: Fully customize with a Lovelace card**
Create a custom card that displays exactly what you want to see.

## Summary

The two "issues" you are observing are actually normal Home Assistant behavior:

- ✅ The Color Picker toggle exists because it is treated as a light
- ✅ The top switch is a quick control (it is the same as the "Switch" below)

None of these elements are bugs — this is simply how Home Assistant works by default.

If you want a fully customized interface, you will need to create a custom Lovelace card or use add-ons such as card-mod.

---

## 🇷🇺 Русский перевод

# О переключателях (switches) в Home Assistant

## Известные проблемы интерфейса

### 1. Переключатель рядом с Color Picker

Переключатель (toggle), который отображается рядом с сущностью "Color Picker", является нативным и обязательным поведением Home Assistant для всех сущностей типа "Light" (освещение).

**Почему существует этот переключатель?**
- Home Assistant рассматривает все Color Picker как источники света
- У всех источников света есть кнопка включения/выключения в интерфейсе
- Нельзя отключить этот переключатель без полного изменения типа сущности

**Возможные решения:**

**Вариант A: Оставить как есть (рекомендуется)**
Переключатель не приносит вреда — он всегда остаётся "ON", потому что Color Picker всегда активен.

**Вариант B: Скрыть переключатель через card-mod (продвинутый способ)**
Установите card-mod и используйте эту конфигурацию в вашем dashboard:

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

**Вариант C: Создать кастомную сущность (очень продвинутый способ)**
Изменить код так, чтобы создать полностью другой тип сущности, не наследующий LightEntity.

### 2. Переключатель сверху рядом с названием устройства

Переключатель, который отображается сверху рядом с названием "esp", не является дополнительным переключателем. Это просто Home Assistant показывает "быстрый доступ" к первой сущности типа switch устройства.

**Что вы видите:**
- Сверху: "esp" с переключателем → быстрый доступ к первому switch
- Ниже: "Switch" → тот же самый переключатель в обычном виде

Это нормальное поведение Home Assistant, предназначенное для быстрого доступа к основным элементам управления устройством.

**Возможные решения:**

**Вариант 1: Игнорировать (рекомендуется)**
Это не ошибка, а функция Home Assistant.

**Вариант 2: Отключить карточку устройства**
Вместо карточки устройства показывайте отдельные сущности:

```yaml
type: entities
entities:
  - entity: switch.esp_switch
  - entity: switch.esp_switch2
  - entity: light.esp_color_picker
  - entity: sensor.esp_gauge
```

**Вариант 3: Полная кастомизация через Lovelace**
Создать собственную карточку, которая отображает всё точно так, как нужно.

## Резюме

Обе "проблемы", которые вы наблюдаете, на самом деле являются нормальным поведением Home Assistant:

- ✅ Переключатель Color Picker существует, потому что это тип "light"
- ✅ Верхний переключатель — это быстрый доступ (тот же самый, что и ниже)

Никакого бага здесь нет — это стандартное поведение системы.

Если нужна полностью кастомная интерфейсная логика, необходимо использовать кастомные карточки Lovelace или расширения вроде card-mod.

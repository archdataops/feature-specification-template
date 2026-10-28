# C4. Уровень 4: код

*Классы ядра одного компонента — только для самой важной или запутанной логики. Это проектный эскиз, а не документация всего кода.*

```plantuml
@startuml
hide empty members
hide circle
' Цвета как у компонентов C4 (уровень 3)
skinparam shadowing false
skinparam roundCorner 10
skinparam ArrowColor #666666
skinparam class {
  BackgroundColor #85BBF0
  BorderColor #78A8D8
  FontColor #000000
  BackgroundColor<<exception>> #999999
  FontColor<<exception>> #FFFFFF
}
skinparam note {
  BackgroundColor #F5F5F5
  BorderColor #999999
}
title Уровень 4. Код: ядро компонента

enum Status {
  STATE_A
  STATE_B
}

class Entity {
  - id : str
  - status : Status
  + action() : None  <<T-01>>
  - _transition(to : Status) : None
}

class TransitionError <<exception>>

Entity --> Status
Entity ..> TransitionError : выбрасывает
@enduml
```

| Элемент | Назначение |
|---------|-----------|
| *Класс или метод* | *Что делает и какой переход, правило или требование реализует* |

> [!TIP]
> Не повторяйте здесь модель данных из раздела 7: там таблицы и поля, здесь — где в коде живёт логика. Хороший кандидат для уровня 4 — статусная модель из раздела 8: один метод на каждый переход и одно место, где проверяется допустимость перехода.


:::mermaid
classDiagram
    Animal <|-- Duck
    Animal <|-- Fish
    Animal <|-- Zebra
    Animal : +int age
    Animal : +String gender
    Animal: +isMammal()
    Animal: +mate()
    class ObjWithSignalToGui{
      +String beakColor
      +swim()
      +quack()
    }
    class GuiWithUpdateAgent{
      +update_gui()
    }
    class Zebra{
      +bool is_wild
      +run()
    }
:::
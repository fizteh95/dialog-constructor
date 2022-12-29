from src.dialogues.scenario_loader import XMLParser
from src.dialogues.domain import Dialogue


def main():
    xml_src_path = "/home/dmitriy/PycharmProjects/dialogue-constructor/src/resources/dialogue-schema-test.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(src_path=xml_src_path)
    dialogue = Dialogue(root_id=root_id, nodes=nodes)
    print(root_id)
    print(dialogue)


if __name__ == '__main__':
    main()

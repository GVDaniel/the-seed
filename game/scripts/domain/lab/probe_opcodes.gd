class_name ProbeOpcodes
extends Object
## Opcodes permitidos. No hay eval ni texto libre ejecutable.

const FORWARD := "AVANZAR"
const TURN_LEFT := "GIRAR_IZQUIERDA"
const TURN_RIGHT := "GIRAR_DERECHA"
const SCAN := "ESCANEAR"
const TRANSMIT := "TRANSMITIR"
const COLLECT := "RECOGER"
const REPEAT_BEGIN := "REPETIR"
const REPEAT_END := "FIN_REPETIR"
const IF_SAMPLE := "SI_MUESTRA"
const IF_END := "FIN_SI"

## Tipos de bloque (colores en la UI).
const CATEGORY_MOVE := "movimiento"
const CATEGORY_ACTION := "accion"
const CATEGORY_CONTROL := "control"


static func basic_set() -> PackedStringArray:
	return PackedStringArray([FORWARD, TURN_LEFT, TURN_RIGHT, SCAN, TRANSMIT, COLLECT])


static func loop_set() -> PackedStringArray:
	return PackedStringArray([REPEAT_BEGIN, REPEAT_END])


static func condition_set() -> PackedStringArray:
	return PackedStringArray([IF_SAMPLE, IF_END])


static func is_known(op: String) -> bool:
	return is_basic(op) or loop_set().has(op) or condition_set().has(op)


static func is_basic(op: String) -> bool:
	return basic_set().has(op)


static func is_block_open(op: String) -> bool:
	return op == REPEAT_BEGIN or op == IF_SAMPLE


static func is_block_close(op: String) -> bool:
	return op == REPEAT_END or op == IF_END


static func closer_for(op: String) -> String:
	match op:
		REPEAT_BEGIN:
			return REPEAT_END
		IF_SAMPLE:
			return IF_END
	return ""


static func category(op: String) -> String:
	match op:
		FORWARD, TURN_LEFT, TURN_RIGHT:
			return CATEGORY_MOVE
		SCAN, TRANSMIT, COLLECT:
			return CATEGORY_ACTION
	return CATEGORY_CONTROL


static func display_name(op: String) -> String:
	match op:
		IF_SAMPLE:
			return "SI hay muestra"
		IF_END:
			return "FIN_SI"
	return op


static func help_text(op: String) -> String:
	match op:
		FORWARD:
			return "Mueve la sonda una casilla hacia donde mira."
		TURN_LEFT:
			return "Gira 90° a la izquierda sin moverse."
		TURN_RIGHT:
			return "Gira 90° a la derecha sin moverse."
		SCAN:
			return "Escanea la casilla (debe tener una estrella)."
		TRANSMIT:
			return "Envía los datos (debe estar en la antena)."
		COLLECT:
			return "Recoge la muestra de la casilla."
		REPEAT_BEGIN:
			return "Repite N veces los bloques hasta FIN_REPETIR."
		IF_SAMPLE:
			return "Hace lo de dentro SOLO si hay muestra aquí."
	return ""

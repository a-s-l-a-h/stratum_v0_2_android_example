import stratum
import stratum._stratum as _s

# =============================================================================
# Global App State & Context
# =============================================================================
activity       = None
res            = None
inflater       = None
current_screen = None

PACKAGE = "com.example.example_xml_ui"

screen_stack        = []
current_layout_info = None
calc_expr           = ""

# =============================================================================
# Helpers
# =============================================================================
def parse_color(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        hex_str = "FF" + hex_str
    val = int(hex_str, 16)
    if val >= 0x80000000:
        val -= 0x100000000
    return val

def get_id(name):
    return res.getIdentifier(name, "id", PACKAGE)

def get_layout(name):
    return res.getIdentifier(name, "layout", PACKAGE)

def find(name):
    if not current_screen: return None
    return current_screen.findViewById(get_id(name))

def as_button(v):
    return _s.android_widget_Button._stratum_cast(v)

def as_textview(v):
    return _s.android_widget_TextView._stratum_cast(v)

def as_edittext(v):
    return _s.android_widget_EditText._stratum_cast(v)

def show_screen(layout_name, setup_fn, add_to_stack=True):
    global current_screen, current_layout_info
    if add_to_stack and current_layout_info:
        screen_stack.append(current_layout_info)
    current_screen = inflater.inflate(get_layout(layout_name), None, False)
    stratum.setContentView(activity, current_screen)
    current_layout_info = (layout_name, setup_fn)
    setup_fn()

def go_back(v=None):
    if len(screen_stack) > 0:
        prev_layout, prev_setup = screen_stack.pop()
        show_screen(prev_layout, prev_setup, add_to_stack=False)
        return True
    return False

def onBackPressed():
    return go_back()

# =============================================================================
# Screen: HOME
# =============================================================================
def setup_home():
    as_button(find("btn_open_calc")).setOnClickListener(
        lambda v: show_screen("screen_calculator", setup_calculator)
    )
    as_button(find("btn_open_bmi")).setOnClickListener(
        lambda v: show_screen("screen_bmi", setup_bmi)
    )

# =============================================================================
# Screen: CALCULATOR
# =============================================================================
def setup_calculator():
    global calc_expr
    calc_expr = ""

    tv_expr   = as_textview(find("calc_expression"))
    tv_result = as_textview(find("calc_result"))

    as_button(find("calc_back")).setOnClickListener(go_back)

    OPERATORS = set('+-×÷')

    def on_calc_press(char):
        global calc_expr

        if char == "C":
            calc_expr = ""
            tv_result.setText("0")
            tv_expr.setText(calc_expr)
            return

        elif char == "=":
            try:
                if calc_expr and calc_expr[-1] in OPERATORS:
                    tv_result.setText("Error")
                    return
                safe_expr = calc_expr.replace("×", "*").replace("÷", "/")
                ans = eval(safe_expr)
                if isinstance(ans, float) and ans.is_integer():
                    ans = int(ans)
                calc_expr = str(ans)
                tv_result.setText(str(ans))
            except Exception:
                tv_result.setText("Error")
                calc_expr = ""

        else:
            if char in OPERATORS and not calc_expr:
                return
            if char in OPERATORS and calc_expr[-1] in OPERATORS:
                return
            calc_expr += char

        tv_expr.setText(calc_expr)

    button_map = {
        "btn_C": "C", "btn_open": "(", "btn_close": ")", "btn_div": "÷",
        "btn_7": "7", "btn_8": "8", "btn_9": "9", "btn_mul": "×",
        "btn_4": "4", "btn_5": "5", "btn_6": "6", "btn_sub": "-",
        "btn_1": "1", "btn_2": "2", "btn_3": "3", "btn_add": "+",
        "btn_0": "0", "btn_dot": ".", "btn_eq": "="
    }

    for view_id, char in button_map.items():
        btn = as_button(find(view_id))
        if btn:
            btn.setOnClickListener(lambda v, c=char: on_calc_press(c))

# =============================================================================
# Screen: BMI
# =============================================================================
def setup_bmi():
    as_button(find("bmi_back")).setOnClickListener(go_back)

    et_weight = as_edittext(find("bmi_input_weight"))
    et_height = as_edittext(find("bmi_input_height"))
    tv_val    = as_textview(find("tv_bmi_value"))
    tv_cat    = as_textview(find("tv_bmi_category"))

    def calculate(v):
        w_str = str(et_weight.getText()).strip()
        h_str = str(et_height.getText()).strip()

        if not w_str or not h_str:
            return

        try:
            w_kg = float(w_str)
            h_cm = float(h_str)
            h_m  = h_cm / 100.0
            bmi  = w_kg / (h_m * h_m)
            bmi_display = round(bmi, 1)

            if bmi < 18.5:
                cat   = "UNDERWEIGHT 🟡"
                color = "#FFB74D"
            elif bmi < 24.9:
                cat   = "NORMAL 🟢"
                color = "#81C784"
            elif bmi < 29.9:
                cat   = "OVERWEIGHT 🟠"
                color = "#FF8A65"
            else:
                cat   = "OBESE 🔴"
                color = "#E57373"

            tv_val.setText(str(bmi_display))
            tv_cat.setText(cat)
            tv_val.setTextColor(parse_color(color))
            tv_cat.setTextColor(parse_color(color))

        except ValueError:
            tv_val.setText("--")
            tv_cat.setText("Invalid Input")
            tv_cat.setTextColor(parse_color("#CF6679"))

    as_button(find("btn_calculate_bmi")).setOnClickListener(calculate)

# =============================================================================
# Lifecycle
# =============================================================================
def onCreate():
    global activity, res, inflater
    activity = stratum.getActivity()
    res      = activity.getResources()
    inflater = activity.getLayoutInflater()
    screen_stack.clear()
    show_screen("screen_home", setup_home, add_to_stack=False)

def onDestroy():
    global activity, res, inflater, current_screen
    activity = res = inflater = current_screen = None
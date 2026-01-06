
from flask import Flask, render_template, request, redirect, url_for, jsonify
from myqueue import Queue
from myqueue import MENU
from binaryTree import BinaryTree, Node
from BST import BinarySearchTree
from BSTmenu import BSTMenuManager
from graph import build_graph, bfs_sp, calculate_fare, compute_travel_time
from quick_sort import quicksort
from bubble_sort import bubblesort
from insertion_sort import insertion_sort as insertion_sort_func
from select_sort import selection_sort

app = Flask(__name__)

# --- Queue setup ---
order_queue = Queue()
bst_manager = BSTMenuManager()
# --- Global course trees ---

sewing_tree = BinaryTree("Learn how to sew")
# Root: Learn how to sew
# L: Sew a dress, R: Sew a pocket
sewing_tree.root.left = Node("Sew a dress")
sewing_tree.root.right = Node("Sew a pocket")
# L->L: Alter a shirt
sewing_tree.root.left.left = Node("Alter a shirt")
# L->L->L: Basic stitches, L->L->R: Basic fabric
sewing_tree.root.left.left.left = Node("Learn basic stitches")
sewing_tree.root.left.left.right = Node("Learn basic fabric types")
# R->L: Sewing machine, R->R: Draping
sewing_tree.root.right.left = Node("Use a sewing machine")
sewing_tree.root.right.right = Node("Learn draping techniques")

# Initialize Drawing Tree
drawing_tree = BinaryTree("Learn how to draw")
drawing_tree.root.left = Node("Perspective drawing")
drawing_tree.root.left.left = Node("One-point perspective")
drawing_tree.root.left.left.left = Node("Sketch basic shapes")
drawing_tree.root.left.left.left.left = Node("Circles & Squares")
drawing_tree.root.left.left.left.right = Node("Own Shapes")
drawing_tree.root.left.right = Node("Two-point perspective")
drawing_tree.root.left.right.left = Node("Sketch basic forms")
drawing_tree.root.left.right.left.left = Node("Cylinder & Cone")
drawing_tree.root.left.right.left.right = Node("Pyramid & Cube")


courses = {
    "Learn how to sew": sewing_tree,
    "Learn how to draw": drawing_tree,
}

default_course = "Learn how to sew"

# Track last selected course
last_selected_course = {"course": default_course}

# --- Helper functions ---
def tree_to_dict(node):
    if node is None:
        return None
    return {
        "value": node.value,
        "completed": getattr(node, "completed", False),
        "left": tree_to_dict(node.left),
        "right": tree_to_dict(node.right)
    }

def gather_nodes_with_paths(node, path=None, out=None):
    if out is None:
        out = []
    if path is None:
        path = []
    if node is None:
        return out
    available_sides = []
    if not node.left: available_sides.append("L")
    if not node.right: available_sides.append("R")
    out.append((node.value, "".join(path), available_sides))
    if node.left:
        gather_nodes_with_paths(node.left, path + ["L"], out=out)
    if node.right:
        gather_nodes_with_paths(node.right, path + ["R"], out=out)
    return out

def convert_tree_to_html(node, current_path=""):
    """Recursively convert BinaryTree nodes to HTML list items with path and status."""
    if node is None:
        return ""
    
    # Determine the CSS class for completed status
    completed_class = "completed-node" if node.completed else ""

    children = ""
    if node.left or node.right:
        children += "<ul>"
        
        # LEFT CHILD
        if node.left:
            left_path = current_path + "L"
            left_children_html = convert_tree_to_html(node.left, left_path)
            # The <a> tag now uses the toggle_goal function via onclick
            children += f"""<li><a href='#' class='{completed_class}' onclick='toggleGoal("{node.left.value}", "{left_path}"); return false;'><span>{node.left.value}</span></a>{left_children_html}</li>"""

        # RIGHT CHILD
        if node.right:
            right_path = current_path + "R"
            right_children_html = convert_tree_to_html(node.right, right_path)
            # The <a> tag now uses the toggle_goal function via onclick
            children += f"""<li><a href='#' class='{completed_class}' onclick='toggleGoal("{node.right.value}", "{right_path}"); return false;'><span>{node.right.value}</span></a>{right_children_html}</li>"""
            
        children += "</ul>"
    return children

def generate_html_tree(tree):
    if not tree or not tree.root:
        return ""

    root_node = tree.root
    root_completed_class = "completed-node" if root_node.completed else ""
    
    # Path for root is empty string ""
    root_children_html = convert_tree_to_html(root_node, "")

    # Root node also gets the click handler. Path is empty string.
    return f"""<ul><li><a href='#' class='{root_completed_class}' onclick='toggleGoal("{root_node.value}", ""); return false;'><span>{root_node.value}</span></a>{root_children_html}</li></ul>"""

# --- Flask routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/sorting')
def sort_page():
    return render_template('sorting.html')

@app.route('/works', methods=['GET', 'POST'])
def works():
    result = None
    if request.method == 'POST':
        operation = request.form.get('operation')
    return render_template('works.html', result=result)

@app.route('/queue', methods=['GET', 'POST'])
def queue_page():
    result = None
    if request.method == 'POST':
        if 'enterOrder' in request.form:
            selected_items = {}
            for item_name in order_queue.MENU.keys():
                quantity = request.form.get(item_name, 0, type=int)
                if quantity > 0:
                    selected_items[item_name] = quantity

            if selected_items:
                order_details = order_queue.enqueue(selected_items)
                wait_mins, wait_secs = divmod(order_details['wait'], 60)
                result = f"Order {order_details['code']} added! Total: P{order_details['total']:.2f}. Est. wait: {int(wait_mins)}m {int(wait_secs)}s"
            else:
                result = "Please select at least one item."
        elif 'finishOrder' in request.form:
            served = order_queue.dequeue()
            if served:
                result = f"Served order {served['code']}"
            else:
                result = "Queue is empty!"
    return render_template(
        'queue.html',
        queue=order_queue.display(),
        result=result,
        menu=order_queue.MENU
    )
@app.route("/toggle_goal/<course_name>/<path:node_path>", methods=["POST"])
@app.route("/toggle_goal/<course_name>/", methods=["POST"]) # Handle root (empty path)
def toggle_goal(course_name, node_path=""):
    # node_path comes in as a string of 'L's and 'R's
    path_list = list(node_path) if node_path else []
    
    # Use the course name stored in the dictionary keys
    tree = courses.get(course_name) 

    if not tree:
        return redirect(url_for('tree_page', result="Error: Course not found."))

    # Find the node using the path
    node_to_toggle = tree.find_by_path(path_list)

    if not node_to_toggle:
        return redirect(url_for('tree_page', result="Error: Node not found."))

    # Apply the logic from binaryTree.py
    result_message = tree.toggle_node(node_to_toggle)
    
    # Update last selected so we stay on this page
    last_selected_course["course"] = course_name
    
    return redirect(url_for('tree_page', result=result_message))


@app.route("/tree", methods=["GET", "POST"])
def tree_page():
    # Only use GET params for initial load. POST actions should start fresh.
    result = request.args.get('result', "") 
    selected_course = last_selected_course["course"]
    
    # Safety check if selected course was deleted
    if selected_course not in courses and courses:
        selected_course = next(iter(courses.keys()))
        last_selected_course["course"] = selected_course
    
    tree = courses.get(selected_course)
    show_custom_panel = False
    
    if request.method == "POST":
        # --- FIX: Clear the result from URL params if we are doing a POST action ---
        result = "" 
        
        # --- DELETE COURSE ---
        delete_course = request.form.get("delete_course")
        if delete_course and delete_course in courses:
            courses.pop(delete_course)
            result = f"Course '{delete_course}' deleted successfully."
            # Pick another course if available
            if courses:
                selected_course = next(iter(courses.keys()))
                last_selected_course["course"] = selected_course
                tree = courses.get(selected_course)
            else:
                selected_course = None
                tree = None

        # --- Course selection ---
        clicked_course = request.form.get("course")
        if clicked_course and clicked_course in courses:
            selected_course = clicked_course
            tree = courses[selected_course]
            last_selected_course["course"] = selected_course
            # Result remains empty here so the popup doesn't reappear

        # --- Show custom panel ---
        if "create_custom" in request.form:
            show_custom_panel = True

        # --- Save custom tree ---
        if "save_custom_tree" in request.form:
            course_title = request.form.get("root_goal", "").strip()
            root_node_value = request.form.get("child_goal", "").strip()
            
            if not course_title or not root_node_value:
                result = "Error: Course Title and Top Goal (Root Node) are mandatory."
                show_custom_panel = True
            elif course_title in courses:
                result = f"Error: Course '{course_title}' already exists."
                show_custom_panel = True
            else:
                new_tree = BinaryTree(root_node_value)
                courses[course_title] = new_tree
                selected_course = course_title
                tree = new_tree
                last_selected_course["course"] = course_title
                show_custom_panel = True
                result = f"Custom course '{course_title}' created."

        # --- Insert node under existing node ---
        parent_path = request.form.get("parent_path")
        new_value = request.form.get("new_value", "").strip()
        side = request.form.get("side")
        
        if parent_path is not None and new_value and tree:
            # Handle empty string for root path
            path_list = list(parent_path) if parent_path else []
            parent_node = tree.find_by_path(path_list)
            
            if parent_node:
                if side == "L":
                    tree.insert_left(parent_node, new_value)
                else:
                    tree.insert_right(parent_node, new_value)
                result = f"Added '{new_value}' under '{parent_node.value}' on {side} side."
                show_custom_panel = True
            elif "new_value" in request.form:
                parent_path = request.form.get("parent_path")
                new_value = request.form.get("new_value", "").strip()
                side = request.form.get("side")  # This might be None if the dropdown failed
            
            if parent_path is not None and new_value and tree:
                path_list = list(parent_path) if parent_path else []
                parent_node = tree.find_by_path(path_list)
                
                if parent_node:
                    # --- STRICT CHECKING START ---
                    if not side:
                        # 1. Catch missing side (Fixes "None side" error)
                        result = "Error: Please select a Side (Left or Right)."
                    
                    elif side == "L":
                        # 2. Check if Left is occupied
                        if parent_node.left is not None:
                            result = f"Error: The Left side of '{parent_node.value}' is already taken!"
                        else:
                            tree.insert_left(parent_node, new_value)
                            result = f"Success: Added '{new_value}' to the Left of '{parent_node.value}'."

                    elif side == "R":
                        # 3. Check if Right is occupied
                        if parent_node.right is not None:
                            result = f"Error: The Right side of '{parent_node.value}' is already taken!"
                        else:
                            tree.insert_right(parent_node, new_value)
                            result = f"Success: Added '{new_value}' to the Right of '{parent_node.value}'."
                    # --- STRICT CHECKING END ---
                    
                    show_custom_panel = True

        # --- DONE button ---
        if "finish_custom" in request.form:
            show_custom_panel = False
            result = f"Custom course '{tree.root.value}' is done."

    # Generate HTML for WHATEVER tree is selected (no more hardcoding)
    tree_html = generate_html_tree(tree) if tree else ""
    nodes_with_paths = gather_nodes_with_paths(tree.root) if tree else []

    return render_template(
        "tree.html",
        result=result,
        courses=list(courses.keys()),
        selected_course=selected_course,
        show_custom_panel=show_custom_panel,
        nodes_with_paths=nodes_with_paths,
        tree_html=tree_html
    )
    
menu_bst = BinarySearchTree()
for item_name in MENU.keys():
    menu_bst.root = menu_bst.insert(menu_bst.root, item_name)


@app.route('/BSTmenu', methods=['GET', 'POST'])
def bst_menu():
    message = None
    
    # 1. Get Categories
    categories = bst_manager.get_categories()
    
    # 2. Determine Selected Category
    selected_category = request.form.get('category') or request.args.get('category')
    if not selected_category and categories:
        selected_category = categories[0]

    # --- ACTION HANDLERS ---
    if request.method == 'POST':
        # A. SET ROOT / REBUILD TREE
        if 'set_root' in request.form:
            chosen_root = request.form.get('root_item')
            bst_manager.reset_tree_with_root(selected_category, chosen_root)
            message = f"Tree rebuilt with Root: {chosen_root}"

        # B. SEARCH ONLY
        elif 'search_name' in request.form:
            name = request.form.get('search_name').strip()
            rt = bst_manager.get_category_root(selected_category)
            found = bst_manager.search_by_name(rt, name)
            message = f"Found: {found}" if found else f"'{name}' not found."

    # 3. Get the specific TREE for this category
    active_root = bst_manager.get_category_root(selected_category)

    # 4. Get Items List for the Dropdown
    category_items = bst_manager.get_items_in_category(selected_category)

    # 5. Stats
    stats = {
        'min': bst_manager.get_min(active_root),
        'max': bst_manager.get_max(active_root),
        'height': bst_manager.get_height(active_root)
    }

    return render_template(
        'BSTmenu.html',
        categories=categories,
        selected_category=selected_category,
        category_items=category_items,
        tree_html=bst_manager.get_tree_html(active_root),
        stats=stats,
        message=message,
        inorder=bst_manager.inorder(active_root),
        preorder=bst_manager.preorder(active_root),
        postorder=bst_manager.postorder(active_root)
    )


# Start of GRAPH
rail_graph = build_graph()
station_info = {
    #LRT1
    "Fernando Poe Jr.": "Landmarks:\nSM City North Edsa\nTriNoma\nQuezon City Memorial Circle",
    "Balintawak": "Landmarks:\nAyala Malls Cloverleaf",
    "Yamaha Monumento": "Landmarks:\nSM City Grand Central\nMonumento Circle\nMalabon Zoo",
    "5th Avenue": "Landmarks:\nThai To Taoist Temple Pagoda\nUng Siu Si Buddhist Temple\nPhilippine Cultural College",
    "R.Papa": "No landmark information available.",
    "Abad Santos": "Landmarks:\nManila Chinese Cemetery",
    "Blumentritt": "Landmarks:\nBlumentritt Flea Market\nManila North Cemetery\nSM San Lazaro",
    "Tayuman": "Landmarks:\nDangwa Flower Market\nDapitan Market\nEspirito Santo Church",
    "Bambang": "Landmarks:\nBambang Medical Supplies\nJose Reyes Memorial Medical Center",
    "Doroteo Jose": "Landmarks:\nDivisoria Mall\nManila Grand Opera Hotel",
    "Carriedo": "Landmarks:\nArroceros Forest Park\nGolden Mosque\nLiwasang Bonifacio",
    "Central Terminal": "Landmarks:\nFort Santiago\nIntramuros\nSM City Manila",
    "United Nations": "Landmarks:\nNational Museums\nRizal Park\nMalacañang Park",
    "Pedro Gil": "Landmarks:\nHyatt Hotel\nRobinsons Place Manila\nUP Manila",
    "Quirino": "Landmarks:\nManila Zoo\nPaco Park\nMalate Church",
    "Vito Cruz": "Landmarks:\nCoconut Palace\nFolk Arts Theater\nHarrison Plaza",
    "Gil Puyat": "Landmarks:\nStar City\nUpside Down Museum\nWorld Trade Center",
    "Libertad": "Landmarks:\nAglipayan Church\nCuneta Astrodome\nJapanese Embassy",
    "EDSA": "Landmarks:\nThe Dessert Museum\nHeritage Hotel\nPhilippine Senate",
    "Baclaran": "Landmarks:\nAyala Malls Manila Bay\nSM Mall of Asia\nSolaire Resort and Casino",
    "Redemptorist-Aseana": "Landmarks:\nOkada Manila\nNational Shrine of Our Mother of Perpetual Help\nAseana City",
    "PITX": "",
    "Ninoy Acquino Avenue": "Landmarks:\nParañaque Cathedral\nDuty Free Philippines Fiestamall Store\nPolytechnic University of the Philippines Parañaque Campus",
    "Dr. Santos": "Landmarks:\nSM City Sucat\nLas Pinas/Parañaque Critical Habitat and Ecotourism Area\nSt. Joseph Parish Church",
    
    #LRT2
    "Recto": "Landmarks:\nRaon Shopping Center\nDEECO Recto\nArranque Market",
    "Legarda": "Landmarks:\nSan Beda University\nLegarda Suites\nSan Sebastian Basilica",
    "Pureza": "Landmarks:\nPUP Main Campus\nEARIST\nSacred Heart of Jesus Parish",
    "V. Mapa": "Landmarks:\nSM City Sta. Mesa\nMezza Residences\nDorm ni Aliah",
    "J. Ruiz": "Pinaglabanan Shrine\nSan Juan City Hall\nSt. John the Baptist Church",
    "Gilmore": "Landmarks:\nGilmore IT Center\nRobinsons Magnolia\nAurora Garden Plaza",
    "Betty-Go Belmonte": "Landmarks:\nCubao Cathedral\nHoly Buddhist Temple\nReligious of the Virgin Mary Motherhouse",
    "LRT Araneta-Center Cubao": "Landmarks:\nSM Cubao\nSmart Araneta Coliseum\nGateway Mall",
    "Anonas": "Landmarks:\nAnonas City Center\nHi-Top Supermart\nTechnological Institute of the Philippines",
    "Katipunan": "Landmarks:\nMiriam College\nUP Diliman\nPhilippine School of Business Administration",
    "Santolan": "Landmarks:\nSM City Marikina\nRiverbanks Center\nMarikina River",
    "Marikina": "Landmarks:\nRobinsons Metro-East\nSta.Lucia East Grand Mall\nAyala Malls Feliz",
    "Antipolo": "Landmarks:\nSM City Masinag\nAntipolo Cathedral\nOur Lady of Fatima University",

    #MRT3   
    "Taft Avenue": "Landmarks:\nNinoy Aquino International Airport\nSM Mall of Asia\nSMX Convention Center",
    "Magallanes": "Landmarks:\nColegio San Agustin-Makati\nAlphaland Makati\nAsia Pacific College",
    "Ayala": "Landmarks:\nAyala Triangle Gardens\nGlorietta\nSM Makati",
    "Buendia": "",
    "Guadalupa": "Landmarks:\nRockwell Center\nRoman Catholic Archdiocese of Manila\nUniversity of Makati",
    "Boni": "Landmarks:\nTV5 Media Center\nRobinsons Cybergate\nParagon Plaza",
    "Shaw Boulevard": "Landmarks:\nShangri-La Plaza\nPavillion Mall\nStarmall Shaw",
    "Ortigas": "Landmarks:\nRobinsons Galleria\nEDSA Shrine",
    "Santolan-Annapolis": "Landmarks:\nCamp Crame\nCamp Aguinaldo\nGreenhills Shopping Center",
    "MRT Araneta-Cubao": "Landmarks:\nSM Cubao\nSmart Araneta Coliseum\nGateway Mall",
    "GMA Kamuning": "Landmarks:\nGMA Network\nQuezon Memorial Circle\nPhilippine Heart Center",
    "Quezon Avenue": "Landmarks:\nUniversity of the Philippines-Diliman\nEton Centris\nPAGASA Complex",
    "North Avenue": "Landmarks:\nSM City North EDSA\nVertis North\nNinoy Aquino Parks and Wildlife Center",
}

@app.route('/graph', methods=['GET', 'POST'])
def graph_page():
    route = None
    error = None
    travel_time = None

    if request.method == 'POST':
        start = request.form.get('start')
        end = request.form.get('end')

        print("START:", start)
        print("END:", end)
        print("IN GRAPH?", start in rail_graph, end in rail_graph)

        if start not in rail_graph or end not in rail_graph:
            error = "Invalid station selected."
        else:
            route = bfs_sp(rail_graph, start, end)
            print("ROUTE:", route)

            if route:
                travel_time = compute_travel_time(route)
            else:
                error = "No connecting route found."

    return render_template(
        'graph.html',
        stations=sorted(rail_graph.keys()),
        route=route,
        error=error,
        station_info=station_info,
        travel_time = travel_time
    )
    
@app.route('/calculate_fare', methods=['POST'])
def get_fare():
    data = request.get_json()
    start = data.get('start')
    end = data.get('end')
    ticket_type = data.get('type')
    
    path = bfs_sp(rail_graph, start, end)
    
    if path:
        cost = calculate_fare(path, ticket_type)
        return jsonify({'fare': cost})
    else:
        return jsonify({'fare': 0})

# Sorting Algos

@app.route('/insertion_sort', methods=['GET', 'POST'])
def insert_sort():
    sorted_nums = None
    original_nums = None

    if request.method == 'POST':
        nums_str = request.form.get('numbers', '').strip()
        if nums_str:
            tokens = nums_str.split()
            original_nums = [int(x) for x in tokens]
            arr = original_nums.copy()
            insertion_sort_func(arr)
            sorted_nums = arr

    return render_template(
        'insertion_sort.html',
        sorted_nums=sorted_nums,
        original_nums=original_nums
    )


@app.route('/merge_sort')
def merge_sort():
    return render_template('merge_sort.html')

@app.route('/selection_sort')
def select_sort():
    return render_template('select_sort.html')

@app.route('/selection_sort_run', methods=['POST'])
def selection_sort_run():
    data = request.get_json()
    array = data.get('array')
    if not array:
        return jsonify({"error": "No numbers provided"}), 400

    from select_sort import selection_sort
    sorted_array, steps = selection_sort(array)
    return jsonify({"sorted_array": sorted_array, "steps": steps})

@app.route('/quick_sort', methods=['GET', 'POST'])
def quick_sort():
    sorted_nums = None
    original_nums = None

    if request.method == 'POST':
        nums_str = request.form.get('numbers')
        original_nums = [int(x.strip()) for x in nums_str.split(',')]
        sorted_nums = quicksort(original_nums)

    return render_template(
        'quick_sort.html',
        sorted_nums=sorted_nums,
        original_nums=original_nums
    )


@app.route('/bubble_sort', methods=['GET', 'POST'])
def bubble_sort():
    sorted_nums = None
    original_nums = None

    if request.method == 'POST':
        nums_str = request.form.get('numbers')
        original_nums = [int(x.strip()) for x in nums_str.split(',')]
        sorted_nums = bubblesort(original_nums)

    return render_template(
        'bubble_sort.html',
        sorted_nums=sorted_nums,
        original_nums=original_nums
    )


@app.route('/big_o')
def big_o():
    return render_template('big_o.html')

if __name__ == "__main__":
    app.run(debug=True, port=5001)






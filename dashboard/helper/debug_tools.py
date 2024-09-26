def print_all_attributes(classInstance):
    print("Class name: ", classInstance.__class__.__name__)
    for attr in dir(classInstance):
        print("obj.%s = %r" % (attr, getattr(classInstance, attr)))

def print_all_attribute_names(classInstance):
    print("Class name: ", classInstance.__class__.__name__)
    print(vars(classInstance).keys())
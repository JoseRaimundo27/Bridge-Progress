def elementos_construidos(model):
    """
    Retorna os elementos físicos de construção do modelo, qualquer que seja o schema.

    A entidade foi renomeada no IFC4X3: IfcBuildingElement (IFC2X3/IFC4) -> IfcBuiltElement (IFC4X3).
    Chamar by_type("IfcBuildingElement") em um IFC4X3 gera um RuntimeError.
    """
    if model.schema.upper().startswith("IFC4X3"):
        return model.by_type("IfcBuiltElement")
    return model.by_type("IfcBuildingElement")

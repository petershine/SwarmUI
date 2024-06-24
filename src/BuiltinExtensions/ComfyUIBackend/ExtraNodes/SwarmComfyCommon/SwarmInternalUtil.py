import comfy, folder_paths, execution
from comfy import samplers

# This is purely a hack to provide a list of embeds in the object_info report.
# Code referenced from Comfy VAE impl. Probably does nothing useful in an actual workflow.
class SwarmEmbedLoaderListProvider:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "embed_name": (folder_paths.get_filename_list("embeddings"), )
            }
        }

    CATEGORY = "SwarmUI/internal"
    RETURN_TYPES = ("EMBEDDING",)
    FUNCTION = "load_embed"

    def load_embed(self, embed_name):
        embed_path = folder_paths.get_full_path("embedding", embed_name)
        sd = comfy.utils.load_torch_file(embed_path)
        return (sd,)


NODE_CLASS_MAPPINGS = {
    "SwarmEmbedLoaderListProvider": SwarmEmbedLoaderListProvider,
}

# Inject CFG++ Samplers
ORIG_SAMPLER_OBJECT = samplers.sampler_object
def sampler_object(name):
    if name == "euler_cfg_pp_regular":
        from comfy_extras import nodes_advanced_samplers
        return samplers.KSAMPLER(nodes_advanced_samplers.sample_euler_cfgpp)
    elif name == "euler_cfg_pp_alt":
        from comfy_extras import nodes_advanced_samplers
        return samplers.KSAMPLER(nodes_advanced_samplers.sample_euler_cfgpp_alt)
    return ORIG_SAMPLER_OBJECT(name)

samplers.sampler_object = sampler_object


# This is a dirty hack to shut up the errors from Dropdown combo mismatch, pending Comfy upstream fix
ORIG_EXECUTION_VALIDATE = execution.validate_inputs
def validate_inputs(prompt, item, validated):
    raw_result = ORIG_EXECUTION_VALIDATE(prompt, item, validated)
    if raw_result is None:
        return None
    (did_succeed, errors, unique_id) = raw_result
    if did_succeed:
        return raw_result
    for error in errors:
        if error['type'] == "return_type_mismatch":
            o_id = error['extra_info']['linked_node'][0]
            o_class_type = prompt[o_id]['class_type']
            if o_class_type == "SwarmInputModelName" or o_class_type == "SwarmInputDropdown":
                errors.remove(error)
    did_succeed = len(errors) == 0
    return (did_succeed, errors, unique_id)

execution.validate_inputs = validate_inputs

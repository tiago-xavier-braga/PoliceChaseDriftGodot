// Port of the Unity DissolveShader graph: noise-based alpha clip driven by `dissolve` (0 = solid, 1 = gone).
shader_type spatial;

uniform sampler2D albedo_texture : source_color, filter_linear_mipmap;
uniform vec4 albedo_color : source_color = vec4(1.0);
uniform float dissolve : hint_range(0.0, 1.0) = 0.0;
uniform float noise_scale = 500.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

float value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
			mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

void fragment() {
	ALBEDO = texture(albedo_texture, UV).rgb * albedo_color.rgb;
	ROUGHNESS = 1.0;
	if (value_noise(UV * noise_scale) < dissolve) {
		discard;
	}
}

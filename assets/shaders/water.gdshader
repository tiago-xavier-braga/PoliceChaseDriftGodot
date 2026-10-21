// Simplified port of the AureDevGames stylized water: scrolling world-space normals, depth-free
// shallow/deep tint, fresnel to the horizon color and light foam from a voronoi texture.
shader_type spatial;
render_mode cull_disabled;

uniform vec4 shallow_color : source_color = vec4(0.0, 0.5715, 0.7057, 1.0);
uniform vec4 deep_color : source_color = vec4(0.0, 0.1785, 0.5623, 1.0);
uniform vec4 foam_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform sampler2D noise_texture : filter_linear_mipmap, repeat_enable;
uniform sampler2D foam_texture : filter_linear_mipmap, repeat_enable;
uniform float normal_scale = 0.05;
uniform float normal_speed = 0.016;
uniform float normal_strength = 0.6;
uniform float foam_tiling = 0.053;
uniform float foam_blend = 0.09;
uniform float fresnel_power = 1.0;
uniform float metallic_value = 0.559;
uniform float smoothness = 0.581;

varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 uv = world_pos.xz * normal_scale;
	float t = TIME * normal_speed;
	float n1 = texture(noise_texture, uv + vec2(t, t * 0.6)).r;
	float n2 = texture(noise_texture, uv * 1.7 - vec2(t * 0.8, t)).r;
	vec3 tangent_normal = normalize(vec3((n1 - 0.5) * normal_strength, (n2 - 0.5) * normal_strength, 1.0));
	NORMAL_MAP = tangent_normal * 0.5 + 0.5;
	float fresnel = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), fresnel_power);
	vec3 color = mix(shallow_color.rgb, deep_color.rgb, fresnel);
	float foam = texture(foam_texture, world_pos.xz * foam_tiling + vec2(t * 2.0)).r;
	color = mix(color, foam_color.rgb, smoothstep(1.0 - foam_blend, 1.0, foam));
	ALBEDO = color;
	METALLIC = metallic_value;
	ROUGHNESS = 1.0 - smoothness;
}

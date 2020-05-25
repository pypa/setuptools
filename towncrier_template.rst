{% for section, _ in sections.items() %}
{% set underline = underlines[0] %}{% if section %}{{section}}
{{ underline * section|length }}
{% endif %}

{% if sections[section] %}
{% for category, val in definitions.items() if category in sections[section]%}
{% if definitions[category]['showcontent'] %}
{% for text, values in sections[section][category].items() %}
* {{ values|join(', ') }}: {{ text }}
{% endfor %}
{% else %}
*  {{ sections[section][category]['']|join(', ') }}

{% endif %}
{% if sections[section][category]|length == 0 %}
No significant changes.
{% else %}
{% endif %}
{% endfor %}

{% else %}
No significant changes.


{% endif %}
{% endfor %}

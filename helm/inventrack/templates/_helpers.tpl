{{/*
Base name for all resources.
Release "inventrack" -> "inventrack", release "staging" -> "staging-inventrack".
*/}}
{{- define "inventrack.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "inventrack.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Labels shared by every resource */}}
{{- define "inventrack.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/name: {{ include "inventrack.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: inventrack
{{- end -}}

{{/*
Selector labels for one component. These must never change after the first install,
so they only contain stable values.
Usage: include "inventrack.selectorLabels" (dict "ctx" . "component" "backend")
*/}}
{{- define "inventrack.selectorLabels" -}}
app.kubernetes.io/name: {{ include "inventrack.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/* Full label set for one component */}}
{{- define "inventrack.componentLabels" -}}
{{ include "inventrack.labels" .ctx }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "inventrack.backendName" -}}{{ include "inventrack.fullname" . }}-backend{{- end -}}
{{- define "inventrack.frontendName" -}}{{ include "inventrack.fullname" . }}-frontend{{- end -}}
{{- define "inventrack.postgresName" -}}{{ include "inventrack.fullname" . }}-postgres{{- end -}}
{{- define "inventrack.dbSecretName" -}}{{ include "inventrack.fullname" . }}-db{{- end -}}
{{- define "inventrack.configMapName" -}}{{ include "inventrack.fullname" . }}-config{{- end -}}

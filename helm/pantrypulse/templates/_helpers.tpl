{{- define "pp.name" -}}
{{- .Release.Name | trunc 40 | trimSuffix "-" -}}
{{- end -}}

{{- define "pp.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/part-of: pantrypulse
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* selector labels: stable across upgrades */}}
{{- define "pp.selector" -}}
app.kubernetes.io/name: {{ .component }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
{{- end -}}

{{- define "pp.dbSecret" -}}
{{- default (printf "%s-db" (include "pp.name" .)) .Values.database.existingSecret -}}
{{- end -}}

{{- define "pp.dbHost" -}}
{{- if .Values.postgres.enabled -}}
{{ include "pp.name" . }}-postgres
{{- else -}}
{{ required "database.externalHost is required when postgres.enabled=false" .Values.database.externalHost }}
{{- end -}}
{{- end -}}

{{- define "pp.backendImage" -}}
{{ .Values.backend.image.repository }}:{{ required "backend.image.tag must be set to the Git commit SHA" .Values.backend.image.tag }}
{{- end -}}

{{- define "pp.frontendImage" -}}
{{ .Values.frontend.image.repository }}:{{ required "frontend.image.tag must be set to the Git commit SHA" .Values.frontend.image.tag }}
{{- end -}}

{{/* Environment shared by the API pods and the migration Job */}}
{{- define "pp.backendEnv" -}}
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "pp.dbSecret" . }}
      key: password
- name: DATABASE_URL
  value: "postgresql+psycopg://{{ .Values.database.user }}:$(DB_PASSWORD)@{{ include "pp.dbHost" . }}:5432/{{ .Values.database.name }}"
- name: GIT_SHA
  value: {{ .Values.backend.image.tag | quote }}
{{- end -}}

{{- define "pp.restrictedContainer" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
runAsNonRoot: true
capabilities:
  drop: ["ALL"]
{{- end -}}

import SOURCE from '../../../backend/resources/template-teaching.json' with {type:'json'};

export const TEMPLATE_CURRICULUM=SOURCE.topics;
export function withTemplateCurriculum(template){
 const lesson=SOURCE.topics[template.id?.replace(/^builtin:/,'')];
 return lesson?{...template,learningPath:template.learningPath||lesson.learningPath,curriculum:lesson,
  explanation:[template.explanation,lesson.markdown].filter(Boolean).join('\n\n')}:template;
}
export const teachingTemplates=templates=>[...templates,...SOURCE.templates].map(withTemplateCurriculum);

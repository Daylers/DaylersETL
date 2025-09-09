select f.id
     , f.report_id
     , f.parent_id
     , f.element_id
     , f.value_s
     , f.schemas_id
     , s.namespace
     , e.element_id as element_path
  from cog_etl2.reports_xml r
       join cog_etl2.facts_xml f on f.report_id = r.id and f.schemas_id = r.schemas_id
       join (select distinct id, namespace from cog_etl2.schemas_xml) s on s.id = r.schemas_id
       join cog_etl2.elements_xml e on e.id = f.element_id
 where r.id in (863)
 order by element_path
 fetch first 40 rows only;
select distinct pl.pkg_sqn
     , ep.data_domain_id
     , f.id as frm_id
     , fs.id as frm_schema_id
     , fe.element_id as element_path
     , fe.id as frm_elements_id
  from etl_wf_pkg_list pl
       join etl_data_flow edf on pl.data_flow_id = edf.data_flow_id
       join etl_pkg ep on ep.pkg_sqn = pl.pkg_sqn and ep.src_layer_id = pl.src_layer_id and ep.data_domain_id = edf.src_data_domain_id
       join frm_schema fs on fs.src_sys_id = ep.src_layer_id and fs.nm = ep.data_domain_id and ep.period_report_dttm between fs.start_dttm and fs.end_dttm
       join frm f on f.id = fs.frm_id and ep.period_report_dttm between f.start_dttm and f.end_dttm
	   	join frm_xml_elements fe on fe.schema_id = fs.id and fe.src_sys_id = 129
 where pl.cwf_run_id = 3560369 --$$CWF_RUN_ID
order by pl.pkg_sqn, ep.data_domain_id, fe.element_id
;


select count(*) from etl_wf_pkg_list
where src_layer_id = 129;

select count(*) from etl_data_flow;

select * from etl_wf_global_param
where param_nm = '$DBConnection_ORA_SOUFR_FSFR_COG_ETL2';

select * from etl_wf_pkg_list
where src_layer_id = 129
and pkg_sqn in (863, 864)
order by pkg_sqn desc;

select * from etl_pkg
where (pkg_sqn = 864 or data_domain_id = 'http://www.it.ru/Schemas/Avior/МФО/OKUD0420890_2_16_5_Neregulyarnaya/2.16.5/1') 
and src_layer_id = 129;

select * from frm_schema
where cd = 'http://www.it.ru/Schemas/Avior/МФО/OKUD0420890_2_16_5_Neregulyarnaya/2.16.5/1';

select * from frm_xsd_element
where id_xsd_file = 158;


select max(id) from frm_xml_elements;

select max(id) from frm;

select max(frm_id) from frm_schema;
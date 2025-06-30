create table if not exists DM.etl_pkg
--on cluster cluster
(
	pkg_sqn Int64 not null comment 'Номер пакета',
	data_domain_id String comment 'Наименование загруженного документа',
	pkg_nm String comment 'Наименование пакета',
	change_dttm Int64 not null comment 'Дата загрузки пакета в днях с 1970.01.01'
)
engine = MergeTree()
partition by change_dttm
order by (pkg_sqn, change_dttm)
primary key pkg_sqn;


select * from DM.etl_pkg
order by pkg_ sqn asc;
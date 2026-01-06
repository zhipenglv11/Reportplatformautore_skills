-- backend/database/alter_professional_data_nullable.sql
-- Allow nullable test_result/test_unit for raw record templates

alter table professional_data
  alter column test_result drop not null,
  alter column test_unit drop not null;

# Copyright 2019 Oihane Crucelaegui - AvanzOSC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from .common import TestCalendarSchoolCommon
from odoo.tests import common
from odoo.exceptions import ValidationError


@common.at_install(False)
@common.post_install(True)
class TestCalendarSchool(TestCalendarSchoolCommon):

    def test_calendar_school(self):
        self.assertEquals(self.student.student_count_meetings, 0)
        self.assertEquals(self.family.family_count_meetings, 0)
        self.assertEquals(self.teacher.count_meetings, 0)
        self.assertEquals(self.tutor.count_meetings, 0)
        self.tutor.generate_meetings()
        self.tutor.invalidate_cache()
        self.assertEquals(self.student.student_count_meetings, 4)
        action_dict = self.student.button_show_meetings()
        self.assertIn(
            ('student_id', 'in', self.student.ids),
            action_dict.get('domain'))
        self.assertEquals(self.family.family_count_meetings, 2)
        action_dict = self.family.button_show_meetings()
        self.assertIn(
            ('family_id', 'in', self.family.ids),
            action_dict.get('domain'))
        self.assertEquals(self.teacher.count_meetings, 4)
        action_dict = self.teacher.button_show_meetings()
        self.assertIn(
            ('teacher_id', 'in', self.teacher.ids),
            action_dict.get('domain'))
        self.assertEquals(self.tutor.count_meetings, 4)
        action_dict = self.tutor.button_show_meetings()
        self.assertIn(
            ('supervised_year_id', 'in', self.tutor.ids),
            action_dict.get('domain'))
        event = self.tutor.meeting_ids[:1]
        self.assertEquals(event.state, 'draft')
        event.action_open()
        self.assertEquals(event.state, 'open')
        self.assertFalse(event.description)
        with self.assertRaises(ValidationError):
            event.action_done()
        event.description = 'Test Description'
        event.action_done()
        self.assertEquals(event.state, 'done')
        event.action_cancel()
        self.assertEquals(event.state, 'cancel')
        event.action_draft()
        self.assertEquals(event.state, 'draft')

    def test_calendar_school_wizard(self):
        self.assertEquals(self.tutor.count_meetings, 0)
        wiz = self.wizard_model.with_context(
            active_ids=self.tutor.ids).create({})
        wiz.meetings_confirm()
        self.tutor.invalidate_cache()
        self.assertEquals(self.tutor.count_meetings, 4)
        cond = [('supervised_year_id', '=', self.tutor[0].id),
                ('teacher_id', '=',  self.tutor[0].teacher_id.id),
                ('student_id', '=', self.tutor[0].student_id.id)]
        calendars = self.calendar_model.search(cond)
        from_date = self.calendar_model.browse(
            min(calendars, key=lambda x: x.start)).start
        to_date = self.calendar_model.browse(
            max(calendars, key=lambda x: x.stop)).stop
        wiz_vals = {'substitute_teacher_id': self.teacher2.id,
                    'from_date': from_date.date(),
                    'to_date': to_date.date()}
        wizard = self.wizard2_model.with_context(
            active_ids=self.tutor.ids).create(wiz_vals)
        wizard.onchange_dates()
        self.assertEquals(len(wizard.lines_ids), 1)
        cond = [('school_year_id', '=', self.tutor[0].school_year_id.id),
                ('teacher_id', '=', self.teacher2.id),
                ('student_id', '=', self.tutor[0].student_id.id)]
        new_tutor_year = self.tutor_model.search(cond)
        if new_tutor_year:
            new_tutor_year.unlink()
        with self.assertRaises(ValidationError):
            wizard.with_context(
                active_ids=self.tutor.ids).change_teacher()
        new_teacher_tutor_year = self.tutor_model.create({
            'student_id': self.tutor[0].student_id.id,
            'teacher_id': self.teacher2.id,
            'school_year_id': self.tutor[0].school_year_id.id})
        wizard.with_context(
            active_ids=self.tutor.ids).change_teacher()
        self.assertEquals(self.tutor.from_date, wizard.from_date)
        self.assertEquals(self.tutor.to_date, wizard.to_date)
        self.assertEquals(
            self.tutor.substitute_teacher_id, wizard.substitute_teacher_id)
        self.assertEquals(calendars.mapped('teacher_id'), self.teacher2)
        self.assertEquals(self.tutor.count_meetings, 0)
        self.assertEquals(new_teacher_tutor_year.count_meetings, 4)
